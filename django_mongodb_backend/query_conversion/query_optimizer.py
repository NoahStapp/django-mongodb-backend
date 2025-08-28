from copy import deepcopy

from django_mongodb_backend.query_conversion.expression_converters import convert_expression


class QueryOptimizer:
    def convert_expr_to_match(self, expr):
        """
        Takes an MQL query with $expr and optimizes it by extracting
        optimizable conditions into separate $match stages.

        Args:
            expr_query: Dictionary containing the $expr query

        Returns:
            List of optimized match conditions
        """
        expr_query = deepcopy(expr)

        if "$expr" not in expr_query:
            return [expr_query]

        if expr_query["$expr"] == {}:
            return [{"$match": {}}]

        expr_content = expr_query["$expr"]

        # Handle the expression content
        match_conditions, remaining_expr_conditions = self._process_expression(expr_content)

        # If there are remaining conditions that couldn't be optimized,
        # keep them in an $expr
        if remaining_expr_conditions:
            print(f"Remaining conditions: {remaining_expr_conditions}, match_conditions: {match_conditions}")
            if len(remaining_expr_conditions) == 1:
                expr_conditions = {"$expr": remaining_expr_conditions[0]}
            else:
                expr_conditions = {"$expr": {"$and": remaining_expr_conditions}}

            if match_conditions:
                # This assumes match_conditions is a list of dicts with $match
                match_conditions[0]["$match"].update(expr_conditions)
            else:
                match_conditions.append({"$match": expr_conditions})

        print(f"Original expr: {expr_query}, optimized expr: {match_conditions}")
        return match_conditions

    def _process_expression(self, expr):
        """
        Process an expression and extract optimizable conditions.

        Args:
            expr: The expression to process
        """
        match_conditions = []
        remaining_conditions = []
        if isinstance(expr, dict):
            # Check if this is an $and operation
            has_and = "$and" in expr
            has_or = "$or" in expr
            # Do a top-level check for $and or $or because these should inform
            # If they fail, they should failover to a remaining conditions list
            # There's probably a better way to do this, but this is a start
            if has_and:
                and_match_conditions, and_remaining_conditions = self._process_logical_conditions(
                    "$and", expr["$and"]
                )
                match_conditions.extend(and_match_conditions)
                remaining_conditions.extend(and_remaining_conditions)
            if has_or:
                or_match_conditions, or_remaining_conditions = self._process_logical_conditions(
                    "$or", expr["$or"]
                )
                match_conditions.extend(or_match_conditions)
                remaining_conditions.extend(or_remaining_conditions)
            if not has_and and not has_or:
                # Process single condition
                optimized = convert_expression(expr)
                if optimized:
                    match_conditions.append({"$match": optimized})
                else:
                    remaining_conditions.append(expr)
        else:
            # Can't optimize
            remaining_conditions.append(expr)
        return match_conditions, remaining_conditions

    def _process_logical_conditions(
        self, logical_op, logical_conditions
    ):
        """
        Process conditions within a logical array.

        Args:
            logical_conditions: List of conditions within logical operator
        """
        optimized_conditions = []
        match_conditions = []
        remaining_conditions = []
        for condition in logical_conditions:
            if isinstance(condition, dict):
                if optimized := convert_expression(condition):
                    optimized_conditions.append(optimized)
                else:
                    remaining_conditions.append(condition)
            else:
                remaining_conditions.append(condition)
        if optimized_conditions:
            match_conditions.append({"$match": {logical_op: optimized_conditions}})
        else:
            remaining_conditions = [{logical_op: logical_conditions}]
        return match_conditions, remaining_conditions