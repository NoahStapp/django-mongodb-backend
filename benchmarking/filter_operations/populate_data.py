from django.db import transaction
from faker import Faker
import random

from benchmarking.common.models import Author
from benchmarking.filter_operations.models import BookOneToOne, BookOneToMany, BookManyToMany

GENRES = [
            "Action", "Comedy", "Drama", "Fantasy", "Horror",
            "Mystery", "Romance", "Sci-Fi", "Thriller", "Western",
            "Adventure", "Animation", "Crime", "Documentary", "Family",
            "History", "Musical", "Sports",
        ]

class DataGenerator:
    """  
    A class to generate random Author and BookOneToOne instances.  
    """

    def __init__(self):
        self.fake = Faker()

    def create_one_to_one_data(self, n):
        """  
        Create n instances one by one

        Args:  
            n (int): Number of instances to create  
        """
        print(f"Creating {n} Author and BookOneToOne instances")

        with transaction.atomic():
            for i in range(n):
                author = Author.objects.create(name=self.fake.name())
                BookOneToOne.objects.create(
                    title=self.fake.sentence(),
                    author=author,
                    genre=self.fake.random_element(GENRES),
                    publish_date=self.fake.date(),
                )

        print(f"Successfully created {n} authors and {n} books!")

    def create_one_to_many_data(self, n):
        print(f"Creating {n} BookOneToMany instances and their authors")

        with transaction.atomic():
            num_books = 0
            while num_books < n:
                author = Author.objects.create(name=self.fake.name())

                for _ in range(random.randint(1, 10)):
                    if num_books >= n:
                        break
                    BookOneToMany.objects.create(
                        title=self.fake.sentence(),
                        author=author,
                        genre=self.fake.random_element(GENRES),
                        publish_date=self.fake.date()
                    )
                    num_books += 1

        print(f"Successfully created {num_books} books and their authors!")

    def create_many_to_many_data(self, n):
        print(f"Creating {n} BookManyToMany instances with multiple authors")

        with transaction.atomic():
            num_books = 0
            while num_books < n:
                authors = [
                    Author.objects.create(name=self.fake.name())
                    for _ in range(random.randint(1, 10))
                ]
                for _ in range(random.randint(1, 10)):
                    if num_books >= n:
                        break
                    BookManyToMany.objects.create(
                        title=self.fake.sentence(),
                        genre=self.fake.random_element(GENRES),
                        publish_date=self.fake.date(),
                        author=authors,
                    )
                    num_books += 1

        print(f"Successfully created {num_books} books with their authors!")

def populate_data(data_type, n):
    """  
    Main function to run the data generation script.  
    """
    generator = DataGenerator()
    book_class = None
    if data_type == "one_to_one":
        book_class = BookOneToOne
    elif data_type == "one_to_many":
        book_class = BookOneToMany
    elif data_type == "many_to_many":
        book_class = BookManyToMany

    print("Starting data generation...")
    print(f"Current counts - Authors: {Author.objects.count()}, Books: {book_class.objects.count()}")

    try:
        if data_type == "one_to_one":
            generator.create_one_to_one_data(n)
        elif data_type == "one_to_many":
            generator.create_one_to_many_data(n)
        elif data_type == "many_to_many":
            generator.create_many_to_many_data(n)
        print("Data generation completed successfully!")
        print(f"Final counts - Authors: {Author.objects.count()}, Books: {book_class.objects.count()}")

    except Exception as e:
        print(f"Error during data generation: {e}")
        raise
