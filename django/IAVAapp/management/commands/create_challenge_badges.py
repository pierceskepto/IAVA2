# django/IAVAapp/management/commands/create_challenge_badges.py
from django.core.management.base import BaseCommand
from IAVAapp.models import Badge

class Command(BaseCommand):
    help = 'Creates badges for daily challenges'

    def handle(self, *args, **kwargs):
        badges = [
            {
                'name': 'Challenge Starter',
                'description': 'Complete your first daily challenge',
                'badge_type': 'special',
                'icon': '🎯',
                'requirement': 1,
                'requirement_field': 'total_challenges_completed'
            },
            {
                'name': 'Week Warrior',
                'description': 'Complete 7 daily challenges in a row',
                'badge_type': 'streak',
                'icon': '⚔️',
                'requirement': 7,
                'requirement_field': 'challenge_streak'
            },
            {
                'name': 'Challenge Champion',
                'description': 'Complete 30 daily challenges',
                'badge_type': 'special',
                'icon': '🏆',
                'requirement': 30,
                'requirement_field': 'total_challenges_completed'
            },
            {
                'name': 'Perfect Week',
                'description': 'Complete 7 daily challenges in a row',
                'badge_type': 'streak',
                'icon': '🌟',
                'requirement': 7,
                'requirement_field': 'challenge_streak'
            },
            {
                'name': 'Monthly Master',
                'description': 'Complete 30 daily challenges in a row',
                'badge_type': 'streak',
                'icon': '📅',
                'requirement': 30,
                'requirement_field': 'challenge_streak'
            },
            {
                'name': 'Challenge Addict',
                'description': 'Complete 100 daily challenges',
                'badge_type': 'special',
                'icon': '💪',
                'requirement': 100,
                'requirement_field': 'total_challenges_completed'
            },
        ]
        
        created_count = 0
        for badge_data in badges:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created badge: {badge.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Badge already exists: {badge.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Successfully created {created_count} new badges!')
        )