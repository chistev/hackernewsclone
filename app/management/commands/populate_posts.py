import random
from django.core.management.base import BaseCommand
from app.models import Post
from django.utils import timezone
import faker


class Command(BaseCommand):
    help = 'Populate the database with sample posts'

    def handle(self, *args, **kwargs):
        fake = faker.Faker()
        platforms = ['shopify', 'alibaba', 'tiktok_shop', 'walmart', 'ebay', 'etsy', 'amazon']

        for _ in range(77):
            title = fake.sentence(nb_words=6)
            url = fake.url()
            platform = random.choice(platforms)
            show_dt = random.choice([True, False])
            ask_dt = random.choice([True, False])
            user_id = 7

            Post.objects.create(
                title=title,
                url=url,
                platform=platform,
                show_dt=show_dt,
                ask_dt=ask_dt,
                user_id=user_id
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with 77 posts.'))
