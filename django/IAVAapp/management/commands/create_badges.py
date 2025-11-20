# Create a management command: IAVAapp/management/commands/create_badges.py
# Run with: python manage.py create_badges

from django.core.management.base import BaseCommand
from IAVAapp.models import Badge

class Command(BaseCommand):
    help = 'Creates initial badges for the gamification system'

    def handle(self, *args, **kwargs):
        badges_to_create = [
            # Streak Badges
            {
                'name': 'Fire Starter',
                'description': 'Complete activities for 3 days in a row',
                'badge_type': 'streak',
                'icon': '🔥',
                'requirement': 3,
                'requirement_field': 'streak_count'
            },
            {
                'name': 'Hot Streak',
                'description': 'Complete activities for 7 days in a row',
                'badge_type': 'streak',
                'icon': '🔥',
                'requirement': 7,
                'requirement_field': 'streak_count'
            },
            {
                'name': 'Inferno',
                'description': 'Complete activities for 30 days in a row',
                'badge_type': 'streak',
                'icon': '🔥',
                'requirement': 30,
                'requirement_field': 'streak_count'
            },
            
            # Accuracy Badges
            {
                'name': 'Sharpshooter',
                'description': 'Achieve 80% accuracy',
                'badge_type': 'accuracy',
                'icon': '🎯',
                'requirement': 80,
                'requirement_field': 'accuracy'
            },
            {
                'name': 'Perfectionist',
                'description': 'Achieve 95% accuracy',
                'badge_type': 'accuracy',
                'icon': '💯',
                'requirement': 95,
                'requirement_field': 'accuracy'
            },
            
            # Level Badges
            {
                'name': 'Rising Star',
                'description': 'Reach Level 5',
                'badge_type': 'level',
                'icon': '⭐',
                'requirement': 5,
                'requirement_field': 'current_level'
            },
            {
                'name': 'Math Wizard',
                'description': 'Reach Level 10',
                'badge_type': 'level',
                'icon': '🧙',
                'requirement': 10,
                'requirement_field': 'current_level'
            },
            {
                'name': 'Math Legend',
                'description': 'Reach Level 20',
                'badge_type': 'level',
                'icon': '👑',
                'requirement': 20,
                'requirement_field': 'current_level'
            },
            
            # XP Badges
            {
                'name': 'Quick Learner',
                'description': 'Earn 1,000 XP',
                'badge_type': 'special',
                'icon': '📚',
                'requirement': 1000,
                'requirement_field': 'xp'
            },
            {
                'name': 'Knowledge Seeker',
                'description': 'Earn 5,000 XP',
                'badge_type': 'special',
                'icon': '📖',
                'requirement': 5000,
                'requirement_field': 'xp'
            },
            {
                'name': 'Master Scholar',
                'description': 'Earn 10,000 XP',
                'badge_type': 'special',
                'icon': '🎓',
                'requirement': 10000,
                'requirement_field': 'xp'
            },
            
            # Special Badges
            {
                'name': 'First Steps',
                'description': 'Complete your first quiz',
                'badge_type': 'special',
                'icon': '👶',
                'requirement': 1,
                'requirement_field': 'total_questions_answered'
            },
            {
                'name': 'Centurion',
                'description': 'Answer 100 questions',
                'badge_type': 'special',
                'icon': '💪',
                'requirement': 100,
                'requirement_field': 'total_questions_answered'
            },
        ]
        
        created_count = 0
        for badge_data in badges_to_create:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created badge: {badge.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Badge already exists: {badge.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} new badges!')
        )