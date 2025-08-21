from copy import deepcopy

from expression_converters import convert_expression


class QueryOptimizer:
    def optimize(self, expr):
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
        match_conditions = []
        remaining_expr_conditions = []

        # Handle the expression content
        self._process_expression(
            expr_content, match_conditions, remaining_expr_conditions
        )

        # If there are remaining conditions that couldn't be optimized,
        # keep them in an $expr
        if remaining_expr_conditions:
            if len(remaining_expr_conditions) == 1:
                expr_conditions = {"$expr": remaining_expr_conditions[0]}
            else:
                expr_conditions = {"$expr": {"$and": remaining_expr_conditions}}

            if match_conditions:
                # This assumes match_conditions is a list of dicts with $match
                match_conditions[0]["$match"].update(expr_conditions)

        return match_conditions

    def _process_expression(self, expr, match_conditions, remaining_conditions):
        """
        Process an expression and extract optimizable conditions.

        Args:
            expr: The expression to process
            match_conditions: List to append optimized match conditions
            remaining_conditions: List to append non-optimizable conditions
        """
        if isinstance(expr, dict):
            # Check if this is an $and operation
            has_and = "$and" in expr
            has_or = "$or" in expr
            # Do a top-level check for $and or $or because these should inform
            # If they fail, they should failover to a remaining conditions list
            # There's probably a better way to do this, but this is a start
            if has_and:
                self._process_logical_conditions(
                    "$and", expr["$and"], match_conditions, remaining_conditions
                )
            if has_or:
                self._process_logical_conditions(
                    "$or", expr["$or"], match_conditions, remaining_conditions
                )
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

    def _process_logical_conditions(
        self, logical_op, logical_conditions, match_conditions, remaining_conditions
    ):
        """
        Process conditions within a logical array.

        Args:
            logical_conditions: List of conditions within logical operator
            match_conditions: List to append optimized match conditions
            remaining_conditions: List to append non-optimizable conditions
        """
        optimized_conditions = []
        for condition in logical_conditions:
            if isinstance(condition, dict):
                if optimized := convert_expression(condition):
                    optimized_conditions.append(optimized)
                else:
                    remaining_conditions.append(condition)
            else:
                remaining_conditions.append(condition)
        match_conditions.append({"$match": {logical_op: optimized_conditions}})


def test_optimizer(optimizer, query, idx):
    """
    Test the QueryOptimizer with various conditions.
    """
    print("Before optimization:")
    pprint(query)
    print("After optimization:")
    pprint(optimizer.optimize(query))
    print()


# Example usage and test cases
if __name__ == "__main__":
    optimizer = QueryOptimizer()
    from pprint import pprint

    # Test case 1: Simple $eq
    query1 = {"$expr": {"$eq": ["$status", "active"]}}, ("Test 1 - Simple $eq:")

    # Test case 2: Simple $in
    query2 = (
        {"$expr": {"$in": ["$category", ["electronics", "books", "clothing"]]}},
        ("Test 2 - Simple $in:"),
    )

    # Test case 3: $and with multiple optimizable conditions
    query3 = (
        {
            "$expr": {
                "$and": [
                    {"$eq": ["$status", "active"]},
                    {"$in": ["$category", ["electronics", "books"]]},
                    {"$eq": ["$verified", True]},
                ]
            }
        },
        ("Test 3 - $and with optimizable conditions:"),
    )

    # Test case 4: Mixed optimizable and non-optimizable conditions
    query4 = (
        {
            "$expr": {
                "$and": [
                    {"$eq": ["$status", "active"]},
                    {"$gt": ["$price", 100]},  # Not optimizable
                    {"$in": ["$category", ["electronics"]]},
                ]
            }
        },
        ("Test 4 - Mixed conditions:"),
    )

    # Test case 5: Non-optimizable condition
    query5 = (
        {"$expr": {"$gt": ["$price", 100]}},
        ("Test 5 - Non-optimizable condition:"),
    )

    # Test case 6: Nested $or conditions
    query6 = (
        {
            "$expr": {
                "$or": [
                    {"$eq": ["$status", "active"]},
                    {"$in": ["$category", ["electronics", "books"]]},
                    {"$and": [{"$eq": ["$verified", True]}, {"$gt": ["$price", 50]}]},
                ]
            }
        },
        ("Test 6 - Nested $or conditions:"),
    )

    # Test case 7: Complex nested conditions with non-optimizable parts
    query7 = (
        {
            "$expr": {
                "$and": [
                    {
                        "$or": [
                            {"$eq": ["$status", "active"]},
                            {"$gt": ["$views", 1000]},
                        ]
                    },
                    {"$in": ["$category", ["electronics", "books"]]},
                    {"$eq": ["$verified", True]},
                    {"$gt": ["$price", 50]},  # Not optimizable
                ]
            }
        },
        ("Test 7 - Complex nested conditions:"),
    )

    # Test case 8: London $in test case
    query8 = (
        {"$expr": {"$in": ["$author_city", ["London"]]}},
        ("Test 8 - London $in test case:"),
    )

    # Test case 9: Deeply nested logical operations
    query9 = (
        {
            "$expr": {
                "$and": [
                    {
                        "$or": [
                            {"$eq": ["$type", "premium"]},
                            {
                                "$and": [
                                    {"$eq": ["$type", "standard"]},
                                    {"$in": ["$region", ["US", "CA"]]},
                                ]
                            },
                        ]
                    },
                    {"$eq": ["$active", True]},
                ]
            }
        },
        ("Test 9 - Deeply nested logical operations:"),
    )

    # Test case 10: Deeply nested logical operations, with Variable!
    query10 = (
        {
            "$expr": {
                "$and": [
                    {
                        "$or": [
                            {"$eq": ["$type", "premium"]},
                            {
                                "$and": [
                                    {"$eq": ["$type", "standard"]},
                                    {"$in": ["$region", ["US", "CA"]]},
                                ]
                            },
                        ]
                    },
                    {"$eq": ["$active", True]},
                ]
            }
        },
        ("Test 10 - Deeply nested logical operations, with Variables!"),
    )

    queries = [
        query1,
        query2,
        query3,
        query4,
        query5,
        query6,
        query7,
        query8,
        query9,
        query10,
    ]

    for idx, (query, description) in enumerate(queries, start=1):
        print(description)
        test_optimizer(optimizer, query, idx)
