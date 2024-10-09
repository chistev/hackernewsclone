import random
from django.core.management.base import BaseCommand
from django.utils import timezone
import faker
from accounts.models import CustomUser
from app.models import Post, Comment


class Command(BaseCommand):
    help = 'Populate the database with sample comments'

    def handle(self, *args, **kwargs):
        fake = faker.Faker()

        # Get all existing posts
        posts = Post.objects.all()
        if not posts.exists():
            self.stdout.write(self.style.WARNING('No posts found. Please create posts first.'))
            return

        # Assuming you have at least one user
        users = CustomUser.objects.all()
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found. Please create users first.'))
            return

        # Delete existing comments
        Comment.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted existing comments.'))

        for _ in range(700):
            content = fake.text(max_nb_chars=200)
            post = random.choice(posts)
            user = random.choice(users)

            # Decide randomly whether to create a reply or a parent comment
            if random.choice([True, False]) and Comment.objects.filter(post=post).exists():
                # Create a reply to an existing comment
                parent_comment = random.choice(Comment.objects.filter(post=post))
                reply = Comment.objects.create(
                    content=content,
                    post=post,
                    user=user,
                    insert_date=timezone.now(),
                    reply=parent_comment  # Set the reply field
                )
            else:
                # Create a parent comment
                reply = Comment.objects.create(
                    content=content,
                    post=post,
                    user=user,
                    insert_date=timezone.now()
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with 700 comments.'))
