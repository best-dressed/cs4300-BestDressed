from django.db import migrations

def convert_old_categories(apps, schema_editor):
    """
    Convert old catalog item categories to new standardized ones.
    
    Old → New mappings:
    - torso → top
    - head → accessory
    - legs → bottom
    - accessory → accessory (no change)
    - shoes → shoes (no change)
    """
    Item = apps.get_model('best_dressed_app', 'Item')
    
    # Mapping of old values to new values
    category_mapping = {
        'torso': 'top',
        'head': 'accessory',
        'legs': 'bottom',
        # These stay the same:
        'accessory': 'accessory',
        'shoes': 'shoes',
    }
    
    for item in Item.objects.all():
        old_tag = item.tag
        if old_tag in category_mapping:
            item.tag = category_mapping[old_tag]
            item.save()
        else:
            # If tag doesn't match any known category, set to 'other'
            item.tag = 'other'
            item.save()

def reverse_conversion(apps, schema_editor):
    """
    Optional: reverse the migration if needed.
    This converts back to old categories.
    """
    Item = apps.get_model('best_dressed_app', 'Item')
    
    reverse_mapping = {
        'top': 'torso',
        'accessory': 'head',  # Arbitrarily choose head for accessories
        'bottom': 'legs',
        'shoes': 'shoes',
    }
    
    for item in Item.objects.all():
        new_tag = item.tag
        if new_tag in reverse_mapping:
            item.tag = reverse_mapping[new_tag]
            item.save()

class Migration(migrations.Migration):

    dependencies = [
        ('best_dressed_app', '0005_item_item_ebay_url_item_item_id_item_seller_id_and_more'),
    ]

    operations = [
        migrations.RunPython(convert_old_categories, reverse_conversion),
    ]