from django.db import transaction
from faker import Faker
import random

from benchmarking.common.models import Author
from benchmarking.one_to_one.models import BookOneToOne


class DataGenerator:
    """  
    A class to generate random Author and BookOneToOne instances.  
    """

    def __init__(self):
        self.fake = Faker()
        # Seed for reproducible results (optional)  
        Faker.seed(42)
        random.seed(42)

    def create_one_to_one_data(self, n):
        """  
        Create n instances one by one

        Args:  
            n (int): Number of instances to create  
        """
        print(f"Creating {n} Author and BookOneToOne instances")

        with transaction.atomic():
            for i in range(n):
                # Create and save author  
                author = Author.objects.create(name=self.fake.name())

                # Create and save book with the author  
                BookOneToOne.objects.create(
                    title=self.fake.sentence(),
                    author=author
                )

                if (i + 1) % 100 == 0:
                    print(f"Created {i + 1} instances...")

        print(f"Successfully created {n} authors and {n} books!")


def populate_data(data_type):
    """  
    Main function to run the data generation script.  
    """
    generator = DataGenerator()

    N = 1000  # Number of instances to generate

    print("Starting data generation...")
    print(f"Current counts - Authors: {Author.objects.count()}, Books: {BookOneToOne.objects.count()}")

    try:
        if data_type == "one_to_one":
            generator.create_one_to_one_data(N)
        print("Data generation completed successfully!")
        print(f"Final counts - Authors: {Author.objects.count()}, Books: {BookOneToOne.objects.count()}")

    except Exception as e:
        print(f"Error during data generation: {e}")
        raise
