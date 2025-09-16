from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.models import User, auth
from django.contrib import messages
import requests
from bs4 import BeautifulSoup as bs
from .models import Product, Github, ProductPriceHistory
import re
from urllib.parse import urlparse
import json
import time
import random
from scrapingbee import ScrapingBeeClient  # Disabled: using requests + BeautifulSoup
from django.conf import settings
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Create your views here.
def index(request):
    if request.method == 'POST':
        product_url = request.POST['product_url']
        user = request.POST['user']
        
        try: # Uncomment for Scrapping Bee integration
            # Basic scraper using requests + BeautifulSoup
            # Previous ScrapingBee-based code kept below for reference:
            # api_url = 'https://app.scrapingbee.com/api/v1/'
            # params = { 'api_key': settings.SCRAPINGBEE_API_KEY, 'url': product_url, 'render_js': 'true',
            #           'premium_proxy': 'true', 'country_code': 'us', 'wait': '3000' }
            # response = requests.get(api_url, params=params, timeout=60)

            # client = ScrapingBeeClient(api_key=settings.SCRAPINGBEE_API_KEY)
            # response = client.get(
            #     url=product_url,
            #     params={
            #         'render_js': 'true',  # If you need JS rendering
            #         'premium_proxy': 'true',
            #         'country_code': 'us',
            #         'wait': '3000'
            #     }
            # )
            # if response.status_code == 200:
            #     soup = bs(response.content, 'html.parser')
            #     product_data = extract_comprehensive_product_data(soup, product_url)

            # Commment for Scrapping Bee integration
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = requests.get(product_url, headers=headers, timeout=40)

            if response.status_code == 200:
                soup = bs(response.text, 'html.parser')
                product_data = extract_comprehensive_product_data(soup, product_url)
            # Till here
                
                # Debug: Print all extracted data
                print("=" * 50)
                print(f"DEBUGGING PRODUCT SCRAPING")
                print(f"URL: {product_url}")
                print(f"Product Name: {product_data['name']}")
                print(f"Image URL: {product_data['image_url']}")
                print(f"Price: {product_data['price']}")
                print(f"Rating: {product_data['rating']}")
                print(f"Reviews: {product_data['reviews']}")
                print("=" * 50)
                
                # Let's also check what images are available in the HTML
                all_images = soup.find_all('img')
                print(f"Found {len(all_images)} images in the page:")
                for i, img in enumerate(all_images[:5]):  # Show first 5 images
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                    alt = img.get('alt', 'No alt text')
                    print(f"  Image {i+1}: {src} (alt: {alt})")
                
                if product_data['name']:
                    # Upsert product for this user+URL so history is accumulated
                    try:
                        existing_product = Product.objects.filter(username=user, product_url=product_url).order_by('-scraped_at').first()
                        if existing_product:
                            existing_product.product_name = product_data['name']
                            existing_product.price = product_data['price']
                            existing_product.original_price = product_data['original_price']
                            existing_product.discount = product_data['discount']
                            existing_product.reviews = product_data['reviews']
                            existing_product.rating = product_data['rating']
                            existing_product.description = product_data['description']
                            existing_product.image_url = product_data['image_url']
                            existing_product.seller = product_data['seller']
                            existing_product.availability = product_data['availability']
                            existing_product.brand = product_data['brand']
                            existing_product.category = product_data['category']
                            existing_product.specifications = product_data['specifications']
                            existing_product.save()
                            new_product = existing_product
                        else:
                            new_product = Product(
                                product_name=product_data['name'],
                                price=product_data['price'],
                                original_price=product_data['original_price'],
                                discount=product_data['discount'],
                                reviews=product_data['reviews'],
                                rating=product_data['rating'],
                                description=product_data['description'],
                                image_url=product_data['image_url'],
                                product_url=product_url,
                                username=user,
                                seller=product_data['seller'],
                                availability=product_data['availability'],
                                brand=product_data['brand'],
                                category=product_data['category'],
                                specifications=product_data['specifications']
                            )
                            new_product.save()
                        # Record price history point for this scrape (enhanced debugging)
                        try:
                            price_value = None
                            if product_data['price']:
                                digits = re.sub(r'[^0-9]', '', str(product_data['price']))
                                if digits:
                                    price_value = int(digits)
                            
                            print(f"🔍 About to create price history entry:")
                            print(f"   - Product ID: {new_product.id}")
                            print(f"   - Product URL: {new_product.product_url}")
                            print(f"   - Price Value: {price_value}")
                            print(f"   - Current Time: {datetime.now()}")
                            
                            # Check existing history before creating new entry
                            existing_history = ProductPriceHistory.objects.filter(product=new_product).order_by('recorded_at')
                            print(f"📊 Existing history entries: {existing_history.count()}")
                            for entry in existing_history:
                                print(f"   - {entry.recorded_at}: {entry.price}")
                            
                            # Always create a new price history entry for each scrape
                            new_entry = ProductPriceHistory.objects.create(product=new_product, price=price_value)
                            print(f"✅ Created NEW price history entry: ID={new_entry.id}, Price={price_value}, Time={new_entry.recorded_at}")
                            
                            # Verify the entry was created
                            all_history = ProductPriceHistory.objects.filter(product=new_product).order_by('recorded_at')
                            print(f"📊 Total price history entries after creation: {all_history.count()}")
                            for entry in all_history:
                                print(f"   - ID: {entry.id}, Time: {entry.recorded_at}, Price: {entry.price}")
                                
                        except Exception as e:
                            print(f"❌ Record price history failed: {e}")
                            import traceback
                            traceback.print_exc()
                    except Exception as e:
                        # Do not block rendering if save fails
                        print(f"Save product failed: {e}")
                    
                    # Enforce per-user limit of 12
                    try:
                        user_products = Product.objects.filter(username=user).order_by('-scraped_at')
                        total = user_products.count()
                        if total > 12:
                            excess = total - 12
                            oldest = Product.objects.filter(username=user).order_by('scraped_at')[:excess]
                            for p in oldest:
                                p.delete()
                    except Exception as e:
                        print(f"Prune products failed: {e}")

                    # Render the home page with success message and a button to product details
                    context = {
                        'user': request.user,
                        'success': True,
                        'clear_form': True,
                        'product_id': new_product.id
                    }
                    messages.success(request, 'Product scraped successfully.')
                    return render(request, 'index.html', context)
                else:
                    messages.error(request, 'Could not extract product details from the provided URL.')
                    return redirect('/')
            else:
                messages.error(request, f'Request failed: {response.status_code}')
                return redirect('/')
                
        except Exception as e:
            messages.error(request, f'Error scraping product: {str(e)}')
        return redirect('/')

    # For GET requests, just render the form
    context = {
        'user': request.user,
        'success': False
    }
    return render(request, 'index.html', context)

def extract_comprehensive_product_data(soup, url):
    """Extract comprehensive product data from various e-commerce websites"""
    product_data = {
        'name': '',
        'price': '',
        'original_price': '',
        'discount': '',
        'reviews': '',
        'rating': '',
        'description': '',
        'image_url': '',
        'seller': '',
        'availability': '',
        'brand': '',
        'category': '',
        'specifications': {}
    }
    
    # Keep original URL for resolving relative image paths later
    product_data['product_url'] = url
    
    # Extract domain to use specific selectors
    domain = urlparse(url).netloc.lower()
    
    # Website-specific extraction
    if 'flipkart' in domain:
        product_data = extract_flipkart_comprehensive_data(soup, product_data)
    elif 'amazon' in domain:
        product_data = extract_amazon_comprehensive_data(soup, product_data)
    elif 'ebay' in domain:
        product_data = extract_ebay_comprehensive_data(soup, product_data)
    elif 'walmart' in domain:
        product_data = extract_walmart_comprehensive_data(soup, product_data)
    elif 'books.toscrape.com' in domain:
        product_data = extract_books_to_scrape_data(soup, product_data)
    else:
        # Generic extraction for other sites
        product_data = extract_generic_product_data(soup, product_data)
    
    # Fallback: Try broader strategies to find a primary image if still missing
    if not product_data.get('image_url'):
        product_data['image_url'] = extract_best_image_url(soup, url)
    
    # Clean up the data
    product_data = clean_comprehensive_product_data(product_data)
    
    return product_data

def extract_books_to_scrape_data(soup, product_data):
    """Extract data from books.toscrape.com product page."""
    try:
        # Title
        title_el = soup.select_one('div.product_main h1')
        if title_el:
            product_data['name'] = title_el.get_text(strip=True)

        # Price (£13.99)
        price_el = soup.select_one('div.product_main p.price_color')
        if price_el:
            product_data['price'] = price_el.get_text(strip=True).replace('£', '₹').replace(',', '')

        # Availability
        avail_el = soup.select_one('div.product_main p.instock.availability')
        if avail_el:
            product_data['availability'] = ' '.join(avail_el.get_text(strip=True).split())

        # Number of reviews from table
        reviews_el = soup.select_one('table.table.table-striped tr:has(th:contains("Number of reviews")) td')
        if reviews_el:
            product_data['reviews'] = reviews_el.get_text(strip=True)

        # Rating is encoded in class on <p class="star-rating Three">
        rating_el = soup.select_one('p.star-rating')
        if rating_el:
            classes = rating_el.get('class', [])
            rating_map = { 'One': '1', 'Two': '2', 'Three': '3', 'Four': '4', 'Five': '5' }
            for cls in classes:
                if cls in rating_map:
                    product_data['rating'] = rating_map[cls]
                    break

        # Description
        desc_h2 = soup.select_one('#product_description')
        if desc_h2:
            para = desc_h2.find_next('p')
            if para:
                product_data['description'] = para.get_text(strip=True)

        # Main image
        img_el = soup.select_one('div.carousel-inner img, div.item.active img, div.thumbnail img, div.product_gallery img')
        if not img_el:
            img_el = soup.select_one('img')
        if img_el:
            src = img_el.get('src')
            if src:
                # Resolve relative URL
                from urllib.parse import urljoin
                product_data['image_url'] = urljoin(product_data.get('product_url', ''), src)

    except Exception:
        pass
    return product_data

# (Removed platform-specific demo extractors for OpenCart and PrestaShop)

def extract_amazon_asin(product_url: str) -> str:
    try:
        m = re.search(r"/(?:dp|gp/product|product)/([A-Z0-9]{10})", product_url)
        if m:
            return m.group(1)
        m2 = re.search(r"/([A-Z0-9]{10})(?:[/?]|$)", product_url)
        return m2.group(1) if m2 else ''
    except Exception:
        return ''


def extract_flipkart_comprehensive_data(soup, product_data):
    """Extract comprehensive data specifically for Flipkart"""
    
    # Product Name - try multiple selectors
    name_selectors = [
        '.B_NuCI', 'h1[class*="title"]', '.product-title', 'h1',
        '[data-testid="product-title"]', '.pdp-product-name',
        '.product-name-text', 'h1[class*="product"]'
    ]
    for selector in name_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['name'] = elem.get_text(strip=True)
            break
    
    # Price - try multiple selectors
    price_selectors = [
        '._30jeq3', '._1vC4OE', '.price', '[class*="price"]',
        '._25b18c', '.a-price-whole', '.a-offscreen'
    ]
    for selector in price_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['price'] = elem.get_text(strip=True)
            break
    
    # Original Price
    original_price_selectors = [
        '._3I9_wc', '._2AcKBi', '.original-price', '[class*="original"]',
        '._3I9_wc._27UcVY', '.a-price-was'
    ]
    for selector in original_price_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['original_price'] = elem.get_text(strip=True)
            break
    
    # Discount
    discount_selectors = [
        '._3Ay6Sb', '.discount', '[class*="discount"]',
        '._3Ay6Sb._27UcVY', '.a-badge-text'
    ]
    for selector in discount_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['discount'] = elem.get_text(strip=True)
            break
    
    # Rating
    rating_selectors = [
        '._2d4LTz', '.rating', '[class*="rating"]',
        '._2d4LTz._27UcVY', '.a-icon-alt'
    ]
    for selector in rating_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['rating'] = elem.get_text(strip=True)
            break
    
    # Reviews
    reviews_selectors = [
        '._2_R_DZ', '.reviews-count', '[class*="review"]',
        '._2_R_DZ._27UcVY', '#acrCustomerReviewText'
    ]
    for selector in reviews_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['reviews'] = elem.get_text(strip=True)
            break
    
    # Description
    desc_selectors = [
        '._1mXcCf', '.product-description', '.description',
        '._1mXcCf._27UcVY', '#feature-bullets'
    ]
    for selector in desc_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['description'] = elem.get_text(strip=True)
            break
    
    # Enhanced Image extraction - try multiple selectors and attributes
    img_selectors = [
        # Flipkart specific selectors
        '.q6DClP img', '._396cs4', '._2r_T1I', '.CXW8mj img',
        '.product-image img', 'img[class*="product"]', 'img[class*="main"]',
        # Generic selectors
        '.a-dynamic-image', '#landingImage', '.product-photo img',
        'img[data-src]', 'img[data-lazy]', 'img[src*="product"]',
        'img[src*="image"]', 'img[alt*="product"]', 'img[alt*="main"]',
        # Additional selectors for different layouts
        'img[class*="img"]', 'img[class*="photo"]', 'img[class*="picture"]',
        'img[src*="amazon"]', 'img[src*="flipkart"]', 'img[src*="ebay"]'
    ]
    
    for selector in img_selectors:
        elem = soup.select_one(selector)
        if elem:
            # Try different attributes for image URL
            img_url = (elem.get('src') or 
                      elem.get('data-src') or 
                      elem.get('data-lazy') or 
                      elem.get('data-original') or
                      elem.get('data-zoom-image'))
            
            if img_url and img_url.strip():
                product_data['image_url'] = img_url.strip()
                break
    
    # If no image found with selectors, try to find any img with product-related attributes
    if not product_data['image_url']:
        all_imgs = soup.find_all('img')
        for img in all_imgs:
            img_url = (img.get('src') or 
                      img.get('data-src') or 
                      img.get('data-lazy') or 
                      img.get('data-original') or
                      img.get('data-zoom-image'))
            
            if img_url and img_url.strip():
                # Check if it looks like a product image
                alt_text = img.get('alt', '').lower()
                if any(keyword in alt_text for keyword in ['product', 'image', 'photo', 'picture', 'main', 'item']):
                    product_data['image_url'] = img_url.strip()
                    break
    
    # Final fallback per-site
    if not product_data['image_url']:
        product_data['image_url'] = extract_best_image_url(soup, product_data.get('product_url', ''))
    
    # Seller
    seller_selectors = [
        '._1RLviY', '.seller', '[class*="seller"]',
        '._1RLviY._27UcVY', '.a-size-small'
    ]
    for selector in seller_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['seller'] = elem.get_text(strip=True)
            break
    
    # Availability
    availability_selectors = [
        '._2JC05C', '.availability', '[class*="stock"]',
        '._2JC05C._27UcVY', '#availability'
    ]
    for selector in availability_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['availability'] = elem.get_text(strip=True)
            break
    
    # Brand
    brand_selectors = [
        '._2d4LTz', '.brand', '[class*="brand"]',
        '._2d4LTz._27UcVY', '.a-size-small'
    ]
    for selector in brand_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            product_data['brand'] = elem.get_text(strip=True)
            break
    
    # Extract specifications
    specs = {}
    spec_rows = soup.select('._1s_Smc, ._2KpZ6l, .row, ._2KpZ6l._27UcVY')
    for row in spec_rows:
        try:
            key_elem = row.select_one('._1hKmbr, .col-3-12, ._1rcQuq')
            value_elem = row.select_one('._21lJbe, .col-9-12, ._2KpZ6l')
            if key_elem and value_elem:
                key = key_elem.get_text(strip=True)
                value = value_elem.get_text(strip=True)
                if key and value:
                    specs[key] = value
        except:
            continue
    
    product_data['specifications'] = specs
    
    return product_data

def extract_amazon_comprehensive_data(soup, product_data):
    """Extract comprehensive data specifically for Amazon"""
    
    # Product Name
    name_elem = soup.select_one('#productTitle')
    if name_elem:
        product_data['name'] = name_elem.get_text(strip=True)
    
    # Price
    price_elem = soup.select_one('.a-price-whole, .a-offscreen')
    if price_elem:
        product_data['price'] = price_elem.get_text(strip=True)
    
    # Original Price
    original_price_elem = soup.select_one('.a-price-was')
    if original_price_elem:
        product_data['original_price'] = original_price_elem.get_text(strip=True)
    
    # Rating
    rating_elem = soup.select_one('.a-icon-alt')
    if rating_elem:
        product_data['rating'] = rating_elem.get_text(strip=True)
    
    # Reviews
    reviews_elem = soup.select_one('#acrCustomerReviewText')
    if reviews_elem:
        product_data['reviews'] = reviews_elem.get_text(strip=True)
    
    # Description
    desc_elem = soup.select_one('#feature-bullets, .a-unordered-list')
    if desc_elem:
        product_data['description'] = desc_elem.get_text(strip=True)
    
    # Enhanced Image extraction for Amazon
    img_selectors = [
        '#landingImage', '.a-dynamic-image', '#imgTagWrapperId img',
        '.a-button-text img', '.a-button-text img', '.a-button-text img',
        'img[data-old-hires]', 'img[data-a-dynamic-image]'
    ]
    
    for selector in img_selectors:
        elem = soup.select_one(selector)
        if elem:
            img_url = (elem.get('src') or 
                      elem.get('data-src') or 
                      elem.get('data-old-hires') or
                      elem.get('data-a-dynamic-image'))
            
            if img_url and img_url.strip():
                product_data['image_url'] = img_url.strip()
                break
    
    # Availability
    availability_elem = soup.select_one('#availability, .a-size-medium')
    if availability_elem:
        product_data['availability'] = availability_elem.get_text(strip=True)
    
    # Fallback
    if not product_data['image_url']:
        product_data['image_url'] = extract_best_image_url(soup, product_data.get('product_url', ''))
    
    return product_data

def extract_ebay_comprehensive_data(soup, product_data):
    """Extract comprehensive data specifically for eBay"""
    
    # Product Name
    name_elem = soup.select_one('#x-title-label-lbl')
    if name_elem:
        product_data['name'] = name_elem.get_text(strip=True)
    
    # Price
    price_elem = soup.select_one('.notranslate')
    if price_elem:
        product_data['price'] = price_elem.get_text(strip=True)
    
    # Image extraction for eBay
    img_elem = soup.select_one('#icImg')
    if img_elem:
        product_data['image_url'] = img_elem.get('src')
    
    return product_data

def extract_walmart_comprehensive_data(soup, product_data):
    """Extract comprehensive data specifically for Walmart"""
    
    # Product Name
    name_elem = soup.select_one('[data-automation-id="product-title"]')
    if name_elem:
        product_data['name'] = name_elem.get_text(strip=True)
    
    # Price
    price_elem = soup.select_one('[itemprop="price"]')
    if price_elem:
        product_data['price'] = price_elem.get_text(strip=True)
    
    # Image extraction for Walmart
    img_elem = soup.select_one('[data-automation-id="product-image"] img')
    if img_elem:
        product_data['image_url'] = img_elem.get('src')
    
    return product_data

def extract_generic_product_data(soup, product_data):
    """Generic extraction for other websites"""
    
    # Common selectors for different websites
    selectors = {
        'name': ['h1', 'h2', '.product-title', '.product-name', '[data-testid="product-title"]'],
        'price': ['.price', '.product-price', '.current-price', '[data-testid="price"]'],
        'rating': ['.rating', '.product-rating', '.star-rating', '[data-testid="rating"]'],
        'reviews': ['.reviews-count', '.review-count', '.rating-count', '[data-testid="review-count"]'],
        'description': ['.product-description', '.product-details', '.description', '[data-testid="description"]'],
        'image': ['.product-image img', '.product-photo img', '.main-image img', '[data-testid="product-image"] img']
    }
    
    for field, field_selectors in selectors.items():
        for selector in field_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if field == 'image':
                        product_data['image_url'] = element.get('src') or element.get('data-src')
                    else:
                        text = element.get_text(strip=True)
                        if text:
                            product_data[field] = text
                            break
            except:
                continue
    
    # Fallback
    if not product_data.get('image_url'):
        product_data['image_url'] = extract_best_image_url(soup, product_data.get('product_url', ''))
    
    return product_data

def extract_best_image_url(soup, page_url):
    """Try multiple strategies (OpenGraph, Twitter, JSON-LD, link rel) to find the best product image URL."""
    try:
        # 1) Open Graph images
        og = soup.select_one('meta[property="og:image"], meta[property="og:image:secure_url"]')
        if og and og.get('content'):
            return og['content'].strip()
        
        # 2) Twitter card
        tw = soup.select_one('meta[name="twitter:image"], meta[name="twitter:image:src"]')
        if tw and tw.get('content'):
            return tw['content'].strip()
        
        # 3) link rel image_src
        link_img = soup.select_one('link[rel="image_src"]')
        if link_img and link_img.get('href'):
            return link_img['href'].strip()
        
        # 4) JSON-LD schema.org Product
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.get_text(strip=True))
            except Exception:
                continue
            candidates = []
            if isinstance(data, dict):
                candidates.append(data)
            elif isinstance(data, list):
                candidates.extend(data)
            for entry in candidates:
                img = entry.get('image') if isinstance(entry, dict) else None
                if isinstance(img, str) and img.strip():
                    return img.strip()
                if isinstance(img, dict) and img.get('url'):
                    return img['url'].strip()
                if isinstance(img, list) and len(img) > 0:
                    first = img[0]
                    if isinstance(first, str):
                        return first.strip()
                    if isinstance(first, dict) and first.get('url'):
                        return first['url'].strip()
        
        # 5) Heuristic: pick a large-looking main image from <img>
        best_url = ''
        best_score = -1
        for img in soup.find_all('img'):
            src = (img.get('src') or img.get('data-src') or img.get('data-lazy') or img.get('data-original') or img.get('data-zoom-image'))
            if not src:
                continue
            url_candidate = src.strip()
            alt_text = (img.get('alt') or '').lower()
            classes = ' '.join(img.get('class', [])).lower()
            width = img.get('width') or img.get('data-width')
            height = img.get('height') or img.get('data-height')
            score = 0
            if any(k in url_candidate.lower() for k in ['main', 'large', 'hero', 'zoom', 'product']):
                score += 5
            if any(k in alt_text for k in ['product', 'image', 'photo', 'picture', 'main', 'item']):
                score += 3
            if any(k in classes for k in ['product', 'image', 'photo', 'picture', 'main', 'hero']):
                score += 2
            try:
                w = int(width) if width else 0
                h = int(height) if height else 0
                if w * h >= 400*400:
                    score += 4
                elif w * h >= 200*200:
                    score += 2
            except Exception:
                pass
            if score > best_score:
                best_score = score
                best_url = url_candidate
        if best_url:
            return best_url
    except Exception:
        pass
    return ''

def clean_comprehensive_product_data(product_data):
    """Clean and format the extracted data"""
    
    # Clean price - remove currency symbols and extra text
    if product_data['price']:
        price_clean = re.sub(r'[^\d.,]', '', product_data['price'])
        product_data['price'] = price_clean
    
    # Clean original price
    if product_data['original_price']:
        original_price_clean = re.sub(r'[^\d.,]', '', product_data['original_price'])
        product_data['original_price'] = original_price_clean
    
    # Clean rating - extract just the number
    if product_data['rating']:
        rating_match = re.search(r'(\d+\.?\d*)', product_data['rating'])
        if rating_match:
            product_data['rating'] = rating_match.group(1)
    
    # Clean reviews - extract just the number
    if product_data['reviews']:
        reviews_match = re.search(r'(\d+)', product_data['reviews'])
        if reviews_match:
            product_data['reviews'] = reviews_match.group(1)
    
    # Enhanced image URL cleaning and validation
    if product_data['image_url']:
        img_url = product_data['image_url'].strip()
        
        # Handle different URL formats
        if img_url.startswith('//'):
            product_data['image_url'] = 'https:' + img_url
        elif img_url.startswith('/'):
            # Try to construct full URL from the original product URL
            from urllib.parse import urlparse
            parsed_url = urlparse(product_data.get('product_url', ''))
            if parsed_url.netloc:
                product_data['image_url'] = 'https://' + parsed_url.netloc + img_url
        elif not img_url.startswith('http'):
            # If it's a relative path without leading slash
            from urllib.parse import urlparse
            parsed_url = urlparse(product_data.get('product_url', ''))
            if parsed_url.netloc:
                base_url = 'https://' + parsed_url.netloc
                if not img_url.startswith('/'):
                    img_url = '/' + img_url
                product_data['image_url'] = base_url + img_url
        
        # Debug: Print the image URL for troubleshooting
        print(f"Final Image URL: {product_data['image_url']}")
    
    return product_data

def image_proxy(request):
    """Proxy remote images to avoid hotlinking/CORS issues while previewing scraped products."""
    url = request.GET.get('url')
    referer = request.GET.get('ref')
    if not url:
        return HttpResponseBadRequest('Missing url')
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
        }
        if referer:
            headers['Referer'] = referer
        resp = requests.get(url, headers=headers, timeout=20, stream=True)
        content_type = resp.headers.get('Content-Type', 'image/jpeg')
        response = HttpResponse(resp.content, content_type=content_type)
        response['Cache-Control'] = 'no-store'
        return response
    except Exception as e:
        return HttpResponseBadRequest(f'Image fetch failed: {str(e)}')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('register')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save();
                return redirect('login')
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('register')
        return redirect('/')
    else:
        return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect('login')

    else:
        return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return redirect('login')

def images(request):
    username = request.user
    products = Product.objects.filter(username=username).order_by('-scraped_at')
    return render(request, 'images.html', {'products': products})

def product_detail(request, product_id):
    """Display detailed product information"""
    try:
        product = Product.objects.get(id=product_id)
        history = ProductPriceHistory.objects.filter(product=product).order_by('recorded_at')
        
        # Debug: Print all price history entries
        print(f"🔍 Price history for product {product_id}:")
        for entry in history:
            print(f"   - {entry.recorded_at}: {entry.price}")
        
        labels = [h.recorded_at.strftime('%d %b %Y') for h in history]
        data = [h.price or 0 for h in history]
        display_price = data[-1] if data else product.price
        last_recorded = history.last().recorded_at if history.exists() else product.scraped_at
        
        print(f"📈 Chart data - Labels: {labels}, Data: {data}")

        # Cross-store comparison (Amazon, Flipkart, eBay)
        comparison_results = compare_prices_across_stores(product.product_name)

        return render(request, 'product_detail.html', {
            'product': product,
            'price_history_labels': labels,
            'price_history_data': data,
            'display_price': display_price,
            'last_recorded': last_recorded,
            'comparison_results': comparison_results
        })
    except Product.DoesNotExist:
        messages.error(request, 'Product not found')
        return redirect('/')

def test_image_url(request):
    """Test function to check if image URLs are working"""
    if request.method == 'POST':
        image_url = request.POST.get('image_url')
        if image_url:
            try:
                response = requests.head(image_url, timeout=10)
                if response.status_code == 200:
                    messages.success(request, f'Image URL is valid: {image_url}')
                else:
                    messages.error(request, f'Image URL returned status {response.status_code}: {image_url}')
            except Exception as e:
                messages.error(request, f'Error testing image URL: {str(e)}')
        else:
            messages.error(request, 'No image URL provided')
    
    return render(request, 'test_image.html')


def compare_prices_across_stores(product_name: str):
    """Lightweight multi-store comparison using first search result from Amazon, Flipkart, and eBay.
    Returns list of dicts: {store, title, price, link, image_url}. Uses ScrapingBee like main scraper.
    """
    results = []
    if not product_name:
        return results

    stores = [
        {
            'name': 'Amazon',
            'search': f"https://www.amazon.in/s?k={quote_plus(product_name)}",
            'result_selector': 'div.s-result-item',
            'title_selector': 'h2 a span',
            'link_selector': 'h2 a',
            'price_selector': 'span.a-price-whole',
            'image_selector': 'img.s-image'
        },
        {
            'name': 'Flipkart',
            'search': f"https://www.flipkart.com/search?q={quote_plus(product_name)}",
            'result_selector': 'div._1AtVbE',
            'title_selector': 'div._4rR01T, a.s1Q9rs',
            'link_selector': 'a',
            'price_selector': 'div._30jeq3',
            'image_selector': 'img'
        },
        {
            'name': 'eBay',
            'search': f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(product_name)}",
            'result_selector': 'li.s-item',
            'title_selector': 'span[role="heading"], h3.s-item__title',
            'link_selector': 'a.s-item__link',
            'price_selector': 'span.s-item__price',
            'image_selector': 'img.s-item__image-img'
        }
    ]

    api_url = 'https://app.scrapingbee.com/api/v1/'
    api_key = getattr(settings, 'SCRAPINGBEE_API_KEY', None)
    if not api_key:
        return results

    for st in stores:
        try:
            params = {
                'api_key': api_key,
                'url': st['search'],
                'render_js': 'true',
                'premium_proxy': 'true',
                'country_code': 'in',
                'wait': '3000'
            }
            r = requests.get(api_url, params=params, timeout=40)
            if r.status_code != 200:
                continue
            soup = bs(r.content, 'html.parser')
            first = soup.select_one(st['result_selector'])
            if not first:
                continue
            title_el = first.select_one(st['title_selector'])
            link_el = first.select_one(st['link_selector'])
            price_el = first.select_one(st['price_selector'])
            img_el = first.select_one(st['image_selector'])
            title = title_el.get_text(strip=True) if title_el else product_name
            link = link_el.get('href') if link_el else st['search']
            if link and link.startswith('/'):
                # Prepend domain
                domain = urlparse(st['search'])._replace(path='', params='', query='', fragment='').geturl()
                link = domain.rstrip('/') + link
            price = price_el.get_text(strip=True) if price_el else ''
            image_url = img_el.get('src') if img_el else ''
            results.append({
                'store': st['name'],
                'title': title,
                'price': price,
                'link': link,
                'image_url': image_url
            })
        except Exception:
            continue

    return results