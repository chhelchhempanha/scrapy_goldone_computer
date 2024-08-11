import scrapy
import json

class GoldoneSpiderSpider(scrapy.Spider):
    name = "goldone_spider"
    allowed_domains = ["www.goldonecomputer.com"]
    start_urls = ["https://www.goldonecomputer.com/"]

    def parse(self, response):
        # Scrape all the main category links
        categories = response.css("ul.dropmenu > li.top_level.dropdown")
        category_links = {}

        for category in categories:
            # Extract the title and link for each category
            link = category.css("li.top_level.dropdown > a.activSub::attr(href)").get()
            title = category.css("li.top_level.dropdown > a.activSub::text").get()
            category_links[title] = link

        # Follow each category link to scrape products
        for title, link in category_links.items():
            yield scrapy.Request(url=link, callback=self.parse_category, meta={'category_title': title})

    def parse_category(self, response):
        category_title = response.meta['category_title']
        # Scrape all product links within the category
        products = response.css("div.product-layout > div.product-block > div.product-block-inner > div.image")

        for product in products:
            # Extract the product link and image
            product_link = product.css("a::attr(href)").get()
            product_image = product.css("a > img::attr(src)").get()

            # Follow the product link to get detailed product information
            yield scrapy.Request(
                url=product_link,
                callback=self.parse_product,
                meta={'category_title': category_title, 'product_image': product_image}
            )

    def parse_product(self, response):
        category_title = response.meta['category_title']
        product_image = response.meta['product_image']

        # Extract product details
        brand = response.css(
            "#content > div.row > div.col-sm-6.product-right > ul:nth-child(3) > li:nth-child(1) > a::text"
        ).get()

        product_name = response.css("#content > div:nth-child(1) > div.col-sm-6.product-right > h3::text").get()
        product_code = response.xpath("//li[span[@class='desc']]/text()").get()
        review_count = response.xpath(
            "//*[@id='content']/div[1]/div[2]/div[1]/a[1]/text()"
        ).get().split(" ")[0]

        # Handle dynamic UI for products with or without discount
        final_price = response.xpath(
            "//*[@id='content']/div[1]/div[2]/ul[2]/li[2]/h3/text()"
        ).get() or response.xpath(
            "//*[@id='content']/div[1]/div[2]/ul[2]/li/h3/text()"
        ).get()

        # Store product data
        product_data = {
            'category_title': category_title,
            'product': {
                'product_name': product_name,
                'final_price': final_price,
                'brand': brand,
                'product_code': product_code,
                'product_image': product_image,
                'review_count': review_count,
            }
        }

        # Save the product data directly to the JSON file
        self.save_product(product_data)

    def save_product(self, product_data):
        # Append product data to the JSON file
        with open('products.json', 'a', encoding='utf-8') as json_file:
            json.dump(product_data, json_file, ensure_ascii=False, indent=4)
            json_file.write(',\n')

    def closed(self, reason):
        # Finalize the JSON file by wrapping it in an array
        with open('products.json', 'r+', encoding='utf-8') as json_file:
            content = json_file.read().strip(',\n')
            json_file.seek(0)
            json_file.write(f'[{content}]')
            json_file.truncate()

