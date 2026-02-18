"""Create comprehensive product data on PythonAnywhere with stock limit 100kg"""
import requests
import time

API_TOKEN = "a0a783bc25a51c6cb5c0e9dc42298c6b18165495"
USERNAME = "rohaannoor123"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}"
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
DOMAIN = f"{USERNAME}.pythonanywhere.com"

script = r'''#!/usr/bin/env python
"""Create comprehensive product data with stock limit 100kg"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'touripk.settings')
sys.path.insert(0, '/home/rohaannoor123/touripk/pkk')
django.setup()

from content.models import Product
from packages.models import Company

# Get companies for assigning products
companies = {c.slug: c for c in Company.objects.all()}
nw = companies.get('northern-ways-tours')
sm = companies.get('smile-miles-travel')
tp = companies.get('touripk-adventures')
pe = companies.get('pakistan-explorers')
mb = companies.get('mountain-breeze-tours')

# Clear existing products and re-create with full data
Product.objects.all().delete()
print("Cleared existing products")

products_data = [
    # === FOOD & BEVERAGES ===
    {
        "name": "Hunza Dried Apricots",
        "description": "Organic sun-dried apricots from the Hunza Valley, known for their exceptional sweet taste and nutritional value. Rich in iron, potassium and Vitamin A. A healthy snack loved worldwide.",
        "price": 599.99,
        "image": "products/dried-apricots.jpg",
        "category": "food",
        "stock_quantity": 200,
        "weight_kg": 0.50,
        "company": nw,
        "is_featured": True,
    },
    {
        "name": "Gilgit Premium Walnuts",
        "description": "Hand-picked premium quality walnuts from the valleys of Gilgit-Baltistan. Naturally dried and unprocessed. Rich in omega-3 fatty acids and antioxidants. Perfect for health-conscious snacking.",
        "price": 899.99,
        "image": "products/Walnuts.jpg",
        "category": "food",
        "stock_quantity": 150,
        "weight_kg": 1.00,
        "company": nw,
        "is_featured": True,
    },
    {
        "name": "Pure Himalayan Shilajit",
        "description": "100% pure Shilajit sourced from the high-altitude rocks of the Himalayan mountains in Northern Pakistan. Known for its energy-boosting and anti-aging properties. Lab tested for purity.",
        "price": 2499.99,
        "image": "products/Shilajit.jpg",
        "category": "food",
        "stock_quantity": 80,
        "weight_kg": 0.10,
        "company": tp,
        "is_featured": True,
    },
    {
        "name": "Hunza Organic Almonds",
        "description": "Fresh organic almonds harvested from the ancient almond orchards of Hunza Valley. These almonds are known for their rich buttery flavor and high nutritional content. No chemicals or preservatives.",
        "price": 1299.99,
        "image": "products/Almond.jpg",
        "category": "food",
        "stock_quantity": 120,
        "weight_kg": 1.00,
        "company": nw,
        "is_featured": True,
    },
    {
        "name": "Skardu Wild Honey",
        "description": "Pure wild honey collected from the mountain flowers of Skardu and Deosai. Unprocessed and raw with natural enzymes intact. Known for its unique floral aroma and medicinal properties.",
        "price": 1800.00,
        "image": "products/Untitled_1.png",
        "category": "food",
        "stock_quantity": 60,
        "weight_kg": 0.75,
        "company": pe,
        "is_featured": True,
    },
    {
        "name": "Chitral Mulberry Pack",
        "description": "Sun-dried mulberries from Chitral Valley. A traditional delicacy packed with vitamins and minerals. Great as a snack or added to cereals, desserts and trail mix.",
        "price": 450.00,
        "image": "products/dried-apricots.jpg",
        "category": "food",
        "stock_quantity": 180,
        "weight_kg": 0.50,
        "company": mb,
        "is_featured": False,
    },
    {
        "name": "Pine Nuts (Chilgoza)",
        "description": "Premium pine nuts (Chilgoza) from the forests of Waziristan. These are among the most expensive nuts in the world, prized for their buttery taste and numerous health benefits.",
        "price": 3500.00,
        "image": "products/Almond.jpg",
        "category": "food",
        "stock_quantity": 50,
        "weight_kg": 0.50,
        "company": tp,
        "is_featured": True,
    },
    {
        "name": "Kalash Valley Cheese",
        "description": "Traditional handmade cheese from the Kalash Valley. Made from pure goat milk using centuries-old recipes. Aged naturally in mountain caves for a distinctive sharp flavor.",
        "price": 950.00,
        "image": "products/products.JPG",
        "category": "food",
        "stock_quantity": 40,
        "weight_kg": 0.50,
        "company": mb,
        "is_featured": False,
    },

    # === HANDICRAFTS ===
    {
        "name": "Swat Emerald Pendant",
        "description": "Handcrafted silver pendant featuring a genuine Swat emerald. Each piece is unique, made by skilled artisans in the Swat Valley. Comes with certificate of authenticity.",
        "price": 5500.00,
        "image": "products/ChatGPT_Image_Oct_12_2025_07_13_10_PM.png",
        "category": "handicrafts",
        "stock_quantity": 25,
        "weight_kg": 0.05,
        "company": sm,
        "is_featured": True,
    },
    {
        "name": "Hunza Handwoven Carpet",
        "description": "Traditional handwoven carpet made by Hunza artisans using pure wool. Features intricate geometric patterns passed down through generations. Each carpet takes 3-6 months to complete.",
        "price": 15000.00,
        "image": "products/Black_And_White_Modern_Fashion_Sale_Banner_Landscape_1.png",
        "category": "handicrafts",
        "stock_quantity": 10,
        "weight_kg": 5.00,
        "company": nw,
        "is_featured": True,
    },
    {
        "name": "Gilgit Woodcarved Box",
        "description": "Beautifully hand-carved decorative wooden box from Gilgit. Made from walnut wood with intricate floral and geometric patterns. Perfect as a jewelry box or decorative piece.",
        "price": 2200.00,
        "image": "products/products_AkSuoAl.JPG",
        "category": "handicrafts",
        "stock_quantity": 35,
        "weight_kg": 0.80,
        "company": pe,
        "is_featured": False,
    },
    {
        "name": "Balochi Embroidery Art Frame",
        "description": "Exquisite Balochi mirror-work embroidery framed as wall art. Vibrant colors and intricate needlework representing centuries of Balochi cultural heritage. Ready to hang.",
        "price": 3800.00,
        "image": "products/products_jndakRS.JPG",
        "category": "handicrafts",
        "stock_quantity": 20,
        "weight_kg": 1.20,
        "company": sm,
        "is_featured": True,
    },
    {
        "name": "Copper Handicraft Plate",
        "description": "Hand-hammered copper decorative plate from Peshawar. Features traditional Islamic art motifs engraved by master craftsmen. Can be used as wall decor or a serving piece.",
        "price": 2800.00,
        "image": "products/add_product.JPG",
        "category": "handicrafts",
        "stock_quantity": 30,
        "weight_kg": 1.50,
        "company": tp,
        "is_featured": False,
    },

    # === CLOTHING ===
    {
        "name": "Chitrali Pakol Cap",
        "description": "Authentic handmade Chitrali Pakol (Chitrali cap) made from pure wool. A cultural icon of Northern Pakistan. Lightweight, warm, and stylish. Available in natural brown color.",
        "price": 800.00,
        "image": "products/add_packages.JPG",
        "category": "clothing",
        "stock_quantity": 100,
        "weight_kg": 0.15,
        "company": mb,
        "is_featured": True,
    },
    {
        "name": "Swat Valley Wool Shawl",
        "description": "Luxurious handwoven pure wool shawl from Swat Valley. Features traditional Pashtun embroidery along the borders. Perfect for cold weather, lightweight yet incredibly warm.",
        "price": 3200.00,
        "image": "products/Untitled_1.png",
        "category": "clothing",
        "stock_quantity": 45,
        "weight_kg": 0.60,
        "company": sm,
        "is_featured": True,
    },
    {
        "name": "Kalash Traditional Dress Set",
        "description": "Replica of the colorful traditional Kalash dress with intricate beadwork and cowrie shell embroidery. Includes headpiece and necklace. A unique cultural souvenir.",
        "price": 6500.00,
        "image": "products/ChatGPT_Image_Oct_12_2025_07_13_10_PM.png",
        "category": "clothing",
        "stock_quantity": 15,
        "weight_kg": 0.80,
        "company": mb,
        "is_featured": False,
    },
    {
        "name": "Gilgit Woolen Socks (3 Pairs)",
        "description": "Handknitted woolen socks from Gilgit. Made from locally sourced sheep wool. Extremely warm and durable, perfect for trekking and winter use. Set of 3 pairs in assorted colors.",
        "price": 650.00,
        "image": "products/products.JPG",
        "category": "clothing",
        "stock_quantity": 200,
        "weight_kg": 0.30,
        "company": pe,
        "is_featured": False,
    },

    # === ACCESSORIES ===
    {
        "name": "Gemstone Prayer Beads (Tasbih)",
        "description": "Beautiful prayer beads (Tasbih) made from genuine semi-precious gemstones sourced from Northern Pakistan. Available in Lapis Lazuli, Jade, and Agate. 33 beads with silver accents.",
        "price": 1500.00,
        "image": "products/add_product.JPG",
        "category": "accessories",
        "stock_quantity": 75,
        "weight_kg": 0.10,
        "company": tp,
        "is_featured": True,
    },
    {
        "name": "Leather Travel Journal",
        "description": "Handcrafted genuine leather travel journal made in Peshawar. Features thick cream pages, a leather strap closure, and a rustic vintage look. Perfect for documenting your Pakistan adventures.",
        "price": 1800.00,
        "image": "products/products_AkSuoAl.JPG",
        "category": "accessories",
        "stock_quantity": 60,
        "weight_kg": 0.40,
        "company": sm,
        "is_featured": False,
    },
    {
        "name": "Truck Art Keychain Set (5 pcs)",
        "description": "Colorful miniature truck art keychains, each hand-painted by Pakistani truck artists. Features classic jingle truck motifs. Set of 5 unique designs. Great souvenirs and gifts.",
        "price": 500.00,
        "image": "products/add_packages.JPG",
        "category": "accessories",
        "stock_quantity": 300,
        "weight_kg": 0.15,
        "company": tp,
        "is_featured": True,
    },

    # === BOOKS & MEDIA ===
    {
        "name": "Pakistan Travel Guide Book",
        "description": "Comprehensive travel guidebook covering all major tourist destinations in Pakistan. Includes maps, itineraries, local tips, accommodation guides and cultural insights. 320 pages, full color.",
        "price": 1200.00,
        "image": "products/products_jndakRS.JPG",
        "category": "books",
        "stock_quantity": 100,
        "weight_kg": 0.55,
        "company": tp,
        "is_featured": False,
    },
    {
        "name": "Northern Pakistan Photo Book",
        "description": "A stunning coffee table book featuring 200+ high-resolution photographs of Northern Pakistan's landscapes, people, and culture. Hardcover with premium matte finish. By renowned photographer Ali Khan.",
        "price": 4500.00,
        "image": "products/Black_And_White_Modern_Fashion_Sale_Banner_Landscape_1.png",
        "category": "books",
        "stock_quantity": 30,
        "weight_kg": 2.00,
        "company": nw,
        "is_featured": True,
    },
]

print(f"Creating {len(products_data)} products...")
for data in products_data:
    # Enforce 100kg stock limit
    max_stock_by_weight = int(100 / data['weight_kg']) if data['weight_kg'] > 0 else 999
    if data['stock_quantity'] > max_stock_by_weight:
        old_qty = data['stock_quantity']
        data['stock_quantity'] = max_stock_by_weight
        print(f"  Stock limited: {data['name']} {old_qty} -> {data['stock_quantity']} (100kg limit at {data['weight_kg']}kg each)")
    
    company = data.pop('company', None)
    p = Product.objects.create(
        **data,
        company=company,
        is_active=True,
        is_approved=True,
    )
    total_weight = p.stock_quantity * p.weight_kg
    print(f"  Created: {p.name} | Cat: {p.category} | Rs.{p.price} | Stock: {p.stock_quantity} | {p.weight_kg}kg ea | Total: {total_weight:.1f}kg")

print(f"\n=== PRODUCT SUMMARY ===")
print(f"Total products: {Product.objects.count()}")
print(f"Active: {Product.objects.filter(is_active=True).count()}")
print(f"Featured: {Product.objects.filter(is_featured=True).count()}")

from django.db.models import Sum, F
total_inv = Product.objects.aggregate(
    total_items=Sum('stock_quantity'),
    total_weight=Sum(F('stock_quantity') * F('weight_kg'))
)
print(f"Total inventory: {total_inv['total_items']} items")
print(f"Total weight: {total_inv['total_weight']:.1f} kg")

print(f"\nBy category:")
for cat, label in Product.CATEGORY_CHOICES:
    count = Product.objects.filter(category=cat).count()
    cat_weight = Product.objects.filter(category=cat).aggregate(w=Sum(F('stock_quantity') * F('weight_kg')))['w'] or 0
    print(f"  {label}: {count} products, {cat_weight:.1f}kg total stock")

print("\nALL DONE!")
'''

# Upload
remote_path = f"/home/{USERNAME}/create_products.py"
url = f"{BASE_URL}/files/path{remote_path}"
resp = requests.post(url, headers=HEADERS, files={"content": ("create_products.py", script.encode(), "text/plain")})
print(f"Script uploaded: {resp.status_code}")

# Run via console
print("\n=== RUNNING ===")
consoles_url = f"{BASE_URL}/consoles/"
resp = requests.get(consoles_url, headers=HEADERS)
consoles = resp.json() if resp.status_code == 200 else []

bash_console = None
for c in consoles:
    if 'bash' in c.get('executable', '').lower():
        bash_console = c['id']
        break

print(f"  Console: {bash_console}")

send_url = f"{BASE_URL}/consoles/{bash_console}/send_input/"
cmd = "cd /home/rohaannoor123/touripk/pkk && source /home/rohaannoor123/.virtualenvs/touripk-venv/bin/activate && python /home/rohaannoor123/create_products.py 2>&1\n"
resp = requests.post(send_url, headers=HEADERS, json={"input": cmd})
print(f"  Sent: {resp.status_code}")

print("  Waiting...")
time.sleep(15)

output_url = f"{BASE_URL}/consoles/{bash_console}/get_latest_output/"
resp = requests.get(output_url, headers=HEADERS)
if resp.status_code == 200:
    output = resp.json().get('output', '')
    print(f"\n{output[-5000:]}")

# Reload
print("\n=== RELOADING ===")
url = f"{BASE_URL}/webapps/{DOMAIN}/reload/"
resp = requests.post(url, headers=HEADERS)
print(f"  Reload: {resp.status_code}")

time.sleep(3)
resp = requests.get(f"https://{DOMAIN}/content/products/", timeout=15)
print(f"\n  Products page: {resp.status_code} ({len(resp.content)} bytes)")
