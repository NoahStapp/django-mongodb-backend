import json
import os
import time
import warnings
from typing import List

from bson import encode
from django.forms import model_to_dict
from django.test import (
    TestCase,
)

from .models import SmallFlatModel, ForeignKeyModel, SmallFlatModelFk, LargeFlatModel

OUTPUT_FILE = os.environ.get("OUTPUT_FILE")

NUM_ITERATIONS = 10
MIN_ITERATION_TIME = 30
MAX_ITERATION_TIME = 60
NUM_DOCS = 10000

result_data: List = []

def tearDownModule():
    output = json.dumps(result_data, indent=4)
    if OUTPUT_FILE:
        with open(OUTPUT_FILE, "w") as opf:
            opf.write(output)
    else:
        print(output)

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
        print(
            f"Completed {self.__class__.__name__} {megabytes_per_sec:.3f} MB/s, MEDIAN={self.percentile(50):.3f}s, "
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
        else:
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
                        f"{self.__class__.__name__} timed out after {MAX_ITERATION_TIME}s, completed {i}/{NUM_ITERATIONS} iterations."
                    )

                break

        self.results = results


class SmallDocTest(PerformanceTest):
    dataset = "small_doc.json"

    def setUp(self):
        super().setUp()
        with open(self.dataset, "r") as data:
            self.document = json.load(data)

        self.data_size = len(encode(self.document)) * NUM_DOCS
        self.field_names = [field.name for field in SmallFlatModel._meta.get_fields() if field.name not in ["id", "field_fk"]]
        self.documents = [self.document.copy() for _ in range(NUM_DOCS)]

class TestSmallDocCreation(SmallDocTest, TestCase):
    def do_task(self):
        for doc in self.documents:
            model = SmallFlatModel()
            for field_name, value in zip(self.field_names, doc.values()):
                setattr(model, field_name, value)
            model.save()

    def after(self):
        SmallFlatModel.objects.all().delete()

class TestSmallDocUpdate(SmallDocTest, TestCase):
    def setUp(self):
        super().setUp()
        for doc in self.documents:
            model = SmallFlatModel()
            for field_name, value in zip(self.field_names, doc.values()):
                setattr(model, field_name, value)
            model.save()
        self.models = list(SmallFlatModel.objects.all())
        self.data_size = len(encode({"field1": "updated_value"})) * NUM_DOCS

    def do_task(self):
        for model in self.models:
            model.field1 = "updated_value"
            model.save()

    def after(self):
        SmallFlatModel.objects.all().delete()

class TestSmallDocFilterById(SmallDocTest, TestCase):
    def setUp(self):
        super().setUp()
        self.ids = []
        for doc in self.documents:
            model = SmallFlatModel()
            for field_name, value in zip(self.field_names, doc.values()):
                setattr(model, field_name, value)
            model.save()
            self.ids.append(model.id)

    def do_task(self):
        for _id in self.ids:
            list(SmallFlatModel.objects.filter(id=_id))

    def tearDown(self):
        super().tearDown()
        SmallFlatModel.objects.all().delete()

class TestSmallDocFilterByForeignKey(SmallDocTest, TestCase):
    def setUp(self):
        super().setUp()
        self.fks = []
        for doc in self.documents:
            model = SmallFlatModelFk()
            for field_name, value in zip(self.field_names, doc.values()):
                if field_name == "field_fk":
                    continue
                setattr(model, field_name, value)
            foreign_key_model = ForeignKeyModel.objects.create(name="foreign_key_name")
            self.fks.append(foreign_key_model)
            foreign_key_model.save()
            setattr(model, "field_fk", foreign_key_model)
            model.save()

    def do_task(self):
        for fk in self.fks:
            list(SmallFlatModelFk.objects.filter(field_fk__id=fk.id))

    def tearDown(self):
        super().tearDown()
        SmallFlatModelFk.objects.all().delete()

class LargeDocTest(PerformanceTest):
    dataset = "large_doc.json"

    def setUp(self):
        super().setUp()
        with open(self.dataset, "r") as data:
            self.document = json.load(data)

        self.data_size = len(encode(self.document)) * NUM_DOCS
        self.documents = [self.document.copy() for _ in range(NUM_DOCS)]

class TestLargeDocCreation(LargeDocTest, TestCase):
    def do_task(self):
        for doc in self.documents:
            model = LargeFlatModel(**doc)
            model.save()

    def after(self):
        LargeFlatModel.objects.all().delete()

class TestLargeDocUpdate(LargeDocTest, TestCase):
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

