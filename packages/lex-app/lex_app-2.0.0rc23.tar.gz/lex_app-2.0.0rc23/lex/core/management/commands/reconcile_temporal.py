from django.core.management.base import BaseCommand
from django.utils import timezone
from lex.process_admin.utils.temporal_reconciler import TemporalReconciler
from datetime import timedelta
from django.apps import apps
import logging

class Command(BaseCommand):
    help = 'Reconciles bitemporal state for records that became active since the last run.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=5,
            help='Lookback window in minutes (default: 5)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Scan ALL history (expensive, use for repair only)',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        
        if options['all']:
            self.stdout.write("Running FULL Temporal Reconciliation...")
            # For full reconciliation, we might use a very old start date
            start_time = now - timedelta(days=365*100) # 100 years ago
        else:
            minutes = options['minutes']
            start_time = now - timedelta(minutes=minutes)
            # Add a small buffer to overlap slightly with previous runs to avoid edge misses
            start_time = start_time - timedelta(seconds=10)
            self.stdout.write(f"Running Temporal Reconciliation (Window: {minutes} mins)...")

        
        # We need a way to scan models. Reconciler scans all models with 'history'.
        
        total_synced = 0
        from django.db import connection
        tables = connection.introspection.table_names()
        
        for model in apps.get_models():
             if hasattr(model, 'history'):
                 history_model = model.history.model
                 # Skip if table missing
                 if history_model._meta.db_table not in tables: continue
                 
                 count = TemporalReconciler.reconcile_model_window(model, start_time, now)
                 if count > 0:
                     self.stdout.write(f"  - {model.__name__}: Synced {count} records")
                     total_synced += count
                     
        self.stdout.write(self.style.SUCCESS(f"Reconciliation Complete. Total Synced: {total_synced}"))
