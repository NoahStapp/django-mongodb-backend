import json
import os
import time
import warnings

from bson import ObjectId, encode
from django.test import (
    TestCase,
)

from .models import (
    ForeignKeyModel,
    IntegerEmbeddedModel,
    LargeFlatModel,
    LargeNestedModel,
    SmallFlatModel,
    SmallFlatModelFk,
    StringEmbeddedModel,
)

OUTPUT_FILE = os.environ.get("OUTPUT_FILE")

NUM_ITERATIONS = 10
MIN_ITERATION_TIME = 30
MAX_ITERATION_TIME = 60
NUM_DOCS = 10000

result_data: list = []


def tearDownModule():
    output = json.dumps(result_data, indent=4)
    if OUTPUT_FILE:
        with open(OUTPUT_FILE, "w") as opf:  # noqa: PTH123
            opf.write(output)
    else:
        print(output)  # noqa: T201


class Timer:
    def __enter__(self):
        self.start = time.monotonic()
        return self

    def __exit__(self, *args):
        self.end = time.monotonic()
        self.interval = self.end - self.start


# Copied from the driver benchmarking suite.
class PerformanceTest:
    dataset: str
    data_size: int

    def setUp(self):
        self.setup_time = time.monotonic()

    def tearDown(self):
        duration = time.monotonic() - self.setup_time
        # Remove "Test" so that TestMyTestName is reported as "MyTestName".
        name = self.__class__.__name__[4:]
        median = self.percentile(50)
        megabytes_per_sec = self.data_size / median / 1000000
        print(  # noqa: T201
            f"Completed {self.__class__.__name__} {megabytes_per_sec:.3f} MB/s, "
            f"MEDIAN={self.percentile(50):.3f}s, "
            f"total time={duration:.3f}s, iterations={len(self.results)}"
        )
        result_data.append(
            {
                "info": {
                    "test_name": name,
                },
                "metrics": [
                    {
                        "name": "megabytes_per_sec",
                        "type": "MEDIAN",
                        "value": megabytes_per_sec,
                        "metadata": {
                            "improvement_direction": "up",
                            "measurement_unit": "megabytes_per_second",
                        },
                    },
                ],
            }
        )

    def before(self):
        pass

    def do_task(self):
        raise NotImplementedError

    def after(self):
        pass

    def percentile(self, percentile):
        if hasattr(self, "results"):
            sorted_results = sorted(self.results)
            percentile_index = int(len(sorted_results) * percentile / 100) - 1
            return sorted_results[percentile_index]
        self.fail("Test execution failed")
        return None

    def runTest(self):
        results = []
        start = time.monotonic()
        i = 0
        while True:
            i += 1
            self.before()
            with Timer() as timer:
                self.do_task()
            self.after()
            results.append(timer.interval)
            duration = time.monotonic() - start
            if duration > MIN_ITERATION_TIME and i >= NUM_ITERATIONS:
                break
            if duration > MAX_ITERATION_TIME:
                with warnings.catch_warnings():
                    warnings.simplefilter("default")
                    warnings.warn(
                        f"{self.__class__.__name__} timed out after {MAX_ITERATION_TIME}s, "
                        f"completed {i}/{NUM_ITERATIONS} iterations.",
                        stacklevel=2,
                    )

                break

        self.results = results


class SmallFlatDocTest(PerformanceTest):
    dataset = "small_doc.json"

    def setUp(self):
        super().setUp()
        with open(self.dataset) as data:  # noqa: PTH123
            self.document = json.load(data)

        self.data_size = len(encode(self.document)) * NUM_DOCS
        self.documents = [self.document.copy() for _ in range(NUM_DOCS)]


class TestSmallFlatDocCreation(SmallFlatDocTest, TestCase):
    def do_task(self):
        for doc in self.documents:
            model = SmallFlatModel(**doc)
            model.save()

    def after(self):
        SmallFlatModel.objects.all().delete()


class TestSmallFlatDocUpdate(SmallFlatDocTest, TestCase):
    def setUp(self):
        super().setUp()
        for doc in self.documents:
            model = SmallFlatModel(**doc)
            model.save()
        self.models = list(SmallFlatModel.objects.all())
        self.data_size = len(encode({"field1": "updated_value"})) * NUM_DOCS

    def do_task(self):
        for model in self.models:
            model.field1 = "updated_value"
            model.save()

    def after(self):
        SmallFlatModel.objects.all().delete()


class TestSmallFlatDocFilterById(SmallFlatDocTest, TestCase):
    def setUp(self):
        super().setUp()
        self.ids = []
        for doc in self.documents:
            model = SmallFlatModel(**doc)
            model.save()
            self.ids.append(model.id)

    def do_task(self):
        for _id in self.ids:
            list(SmallFlatModel.objects.filter(id=_id))

    def tearDown(self):
        super().tearDown()
        SmallFlatModel.objects.all().delete()


class TestSmallFlatDocFilterByForeignKey(SmallFlatDocTest, TestCase):
    def setUp(self):
        super().setUp()
        self.fks = []
        for doc in self.documents:
            model = SmallFlatModelFk(**doc)
            foreign_key_model = ForeignKeyModel.objects.create(name="foreign_key_name")
            self.fks.append(foreign_key_model)
            foreign_key_model.save()
            model.field_fk = foreign_key_model
            model.save()

    def do_task(self):
        for fk in self.fks:
            list(SmallFlatModelFk.objects.filter(field_fk__id=fk.id))

    def tearDown(self):
        super().tearDown()
        SmallFlatModelFk.objects.all().delete()
        ForeignKeyModel.objects.all().delete()


class LargeFlatDocTest(PerformanceTest):
    dataset = "large_doc.json"

    def setUp(self):
        super().setUp()
        with open(self.dataset) as data:  # noqa: PTH123
            self.document = json.load(data)

        self.data_size = len(encode(self.document)) * NUM_DOCS
        self.documents = [self.document.copy() for _ in range(NUM_DOCS)]


class TestLargeFlatDocCreation(LargeFlatDocTest, TestCase):
    def do_task(self):
        for doc in self.documents:
            model = LargeFlatModel(**doc)
            model.save()

    def after(self):
        LargeFlatModel.objects.all().delete()


class TestLargeFlatDocUpdate(LargeFlatDocTest, TestCase):
    def setUp(self):
        super().setUp()
        for doc in self.documents:
            model = LargeFlatModel(**doc)
            model.save()
        self.models = list(LargeFlatModel.objects.all())
        self.data_size = len(encode({"field1": "updated_value"})) * NUM_DOCS

    def do_task(self):
        for model in self.models:
            model.field1 = "updated_value"
            model.save()

    def after(self):
        LargeFlatModel.objects.all().delete()


class LargeNestedDocTest(PerformanceTest):
    dataset = "large_doc_nested.json"

    def setUp(self):
        super().setUp()
        with open(self.dataset) as data:  # noqa: PTH123
            self.document = json.load(data)

        self.data_size = len(encode(self.document)) * NUM_DOCS
        self.documents = [self.document.copy() for _ in range(NUM_DOCS)]

    def create_model(self):
        for doc in self.documents:
            model = LargeNestedModel()
            for k, v in doc.items():
                if "array" in k:
                    array_models = []
                    for item in v:
                        embedded_str_model = StringEmbeddedModel(**item)
                        embedded_str_model.unique_id = ObjectId()
                        array_models.append(embedded_str_model)
                    setattr(model, k, array_models)
                elif "str" in k:
                    embedded_str_model = StringEmbeddedModel(**v)
                    embedded_str_model.unique_id = ObjectId()
                    setattr(model, k, embedded_str_model)
                else:
                    embedded_int_model = IntegerEmbeddedModel(**v)
                    embedded_int_model.unique_id = ObjectId()
                    setattr(model, k, embedded_int_model)
            model.save()


class TestLargeNestedDocCreation(LargeNestedDocTest, TestCase):
    def do_task(self):
        self.create_model()

    def after(self):
        LargeNestedModel.objects.all().delete()


class TestLargeNestedDocUpdate(LargeNestedDocTest, TestCase):
    def setUp(self):
        super().setUp()
        self.create_model()
        self.models = list(LargeNestedModel.objects.all())
        self.data_size = len(encode({"field1": "updated_value"})) * NUM_DOCS

    def after(self):
        LargeNestedModel.objects.all().delete()

    def do_task(self):
        for model in self.models:
            model.embedded_str_doc_1.field1 = "updated_value"
            model.save()


class TestLargeNestedDocFilterById(LargeNestedDocTest, TestCase):
    def setUp(self):
        super().setUp()
        self.create_model()
        self.ids = [
            model.embedded_str_doc_1.unique_id for model in list(LargeNestedModel.objects.all())
        ]

    def do_task(self):
        for _id in self.ids:
            list(LargeNestedModel.objects.filter(embedded_str_doc_1__unique_id=_id))

    def tearDown(self):
        super().tearDown()
        LargeNestedModel.objects.all().delete()


class TestLargeNestedDocFilterArray(LargeNestedDocTest, TestCase):
    def setUp(self):
        super().setUp()
        self.create_model()
        self.ids = [
            model.embedded_str_doc_array[0].unique_id
            for model in list(LargeNestedModel.objects.all())
        ]

    def do_task(self):
        for _id in self.ids:
            list(LargeNestedModel.objects.filter(embedded_str_doc_array__unique_id__in=[_id]))

    def tearDown(self):
        super().tearDown()
        LargeNestedModel.objects.all().delete()
