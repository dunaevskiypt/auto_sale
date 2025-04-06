import scrapy
import re
from datetime import datetime
from scrapy.exporters import JsonItemExporter


class SprintParser(scrapy.Spider):
    name = "sprint_spider"
    allowed_domains = ["auto.ria.com"]

    def __init__(self):
        # Create a dictionary to store exporters for each category
        self.exporters = {}
        self.empty_pages_count = {}  # To track empty pages for each category

    def start_requests(self):
        # List of categories with ids and names
        category_ids = {
            1: "cars",  # Cars
            2: "motorbikes",  # Motorbikes
            6: "trucks",  # Trucks
            7: "buses"  # Buses
        }

        base_url = "https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id={category_id}&custom=1&abroad=2"

        # Initialize exporters for each category
        for category_id, category_name in category_ids.items():
            file = open(f"sprint_data_{category_name}.json", "wb")
            exporter = JsonItemExporter(file, ensure_ascii=False, indent=4)
            exporter.start_exporting()
            self.exporters[category_id] = (exporter, file)
            # Initialize empty page count for each category
            self.empty_pages_count[category_id] = 0

            # Request pages for each category
            # Set a reasonable page limit based on the category (e.g., 3200 for cars, 200 for motorbikes)
            page_limit = 320 if category_id == 1 else 200  # Adjust this limit per category
            for page in range(0, page_limit + 1):
                url = base_url.format(page=page, category_id=category_id)
                yield scrapy.Request(url, callback=self.parse_page, dont_filter=True, cb_kwargs={"category_id": category_id})

    def parse_page(self, response, category_id):
        items = response.css("section.ticket-item")

        # Check if the page is empty (no items)
        if not items:
            self.empty_pages_count[category_id] += 1
            self.logger.info(
                f"Page {response.url} is empty. Empty pages in category {category_id}: {self.empty_pages_count[category_id]}"
            )

            # If we encounter 50 consecutive empty pages, stop parsing for this category
            if self.empty_pages_count[category_id] >= 50:
                self.logger.info(
                    f"More than 50 consecutive empty pages in category {category_id}, moving to next category."
                )
                # Skip to the next category (don't stop the entire spider)
                return

        else:
            # Reset empty page count if items are found
            self.empty_pages_count[category_id] = 0

        # Get the exporter for this category
        exporter, _ = self.exporters[category_id]

        for item in items:
            data = self.extract_data(item)
            data["category_id"] = category_id  # Add category_id to each record
            exporter.export_item(data)
            yield data

    def extract_data(self, item):
        title = item.css("a.address::attr(title)").get()
        brand, model, year = self.extract_title_info(title)
        generation = self.extract_text(item, "div.generation span::text")
        price = self.extract_price(item)
        mileage = self.extract_mileage(item)
        fuel_type, transmission, engine_capacity = self.extract_characteristics(
            item)
        location = self.extract_location(item)
        state_number = self.extract_text(item, "span.state-num.ua::text")
        vin_code = self.extract_text(item, "span.label-vin span::text")
        add_date, update_date = self.extract_dates(item)
        was_in_accident = self.extract_accident_status(item)
        top_lifts = self.extract_promotion_level(item)
        sale_status, sale_date = self.extract_sale_status(item)

        return {
            "id": item.attrib.get("data-advertisement-id"),
            "brand": brand,
            "model": model,
            "year": year,
            "generation": generation,
            "price": price,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "engine_capacity": engine_capacity,
            "location": location,
            "state_number": state_number,
            "vin_code": vin_code,
            "add_date": add_date,
            "update_date": update_date,
            "was_in_accident": was_in_accident,
            "top_lifts": top_lifts,
            "sale_status": sale_status,
            "sale_date": sale_date,
        }

    def extract_title_info(self, title):
        if title:
            parts = title.split(" ", 2)
            brand = parts[0]
            model = parts[1] if len(parts) > 1 else None
            year_match = re.search(r'\b\d{4}\b', title)
            year = int(year_match.group()) if year_match else None
            return brand, model, year
        return None, None, None

    def extract_text(self, item, selector):
        text = item.css(selector).get()
        return text.strip() if text else None

    def extract_price(self, item):
        price_text = item.css("span[data-currency='USD']::text").get()
        return int(price_text.strip().replace(" ", "")) if price_text else None

    def extract_mileage(self, item):
        mileage_text = item.css("li.item-char.js-race::text").get()
        mileage_match = re.search(
            r"(\d+)\s*тис\. км", mileage_text) if mileage_text else None
        return int(mileage_match.group(1)) * 1000 if mileage_match else None

    def extract_characteristics(self, item):
        characteristics = item.css(
            "ul.unstyle.characteristic li.item-char::text").getall()
        fuel_type, transmission, engine_capacity = None, None, None
        for char in characteristics:
            char = char.strip()
            if char in ["Бензин", "Дизель", "Газ", "Електро"]:
                fuel_type = char
            engine_match = re.search(r"(\d+[.,]?\d*)\s*л\.", char)
            if engine_match:
                engine_capacity = int(
                    float(engine_match.group(1).replace(',', '.')) * 1000)
            if char in ["Автомат", "Механіка", "Варіатор"]:
                transmission = char
        return fuel_type, transmission, engine_capacity

    def extract_location(self, item):
        location = item.xpath(
            ".//li[contains(@class, 'js-location')]//text()[normalize-space()]").getall()
        location_text = " ".join(location).strip() if location else None
        if location_text:
            location_text = re.sub(r"[^\w\s]", "", location_text)
            location_text = location_text.split("від")[0].strip()
        return location_text

    def extract_dates(self, item):
        add_date = self.extract_text(
            item, "span[data-add-date]::attr(data-add-date)")
        update_date = self.extract_text(
            item, "span[data-update-date]::attr(data-update-date)")
        return (datetime.strptime(add_date, "%Y-%m-%d %H:%M:%S") if add_date else None,
                datetime.strptime(update_date, "%Y-%m-%d %H:%M:%S") if update_date else None)

    def extract_accident_status(self, item):
        accident = self.extract_text(item, "span.state._red::text")
        return "Був в ДТП" in accident if accident else False

    def extract_promotion_level(self, item):
        promotion = self.extract_text(
            item, "a.item.small-promote-level::attr(title)")
        return int(promotion) if promotion and promotion.isdigit() else 0

    def extract_sale_status(self, item):
        sold_date = self.extract_text(
            item, "span[data-sold-date]::attr(data-sold-date)")
        return ("sold", datetime.strptime(sold_date, "%Y-%m-%d %H:%M:%S")) if sold_date else ("on_sale", None)

    def close(self, reason):
        # Close all files and exporters for each category
        for exporter, file in self.exporters.values():
            exporter.finish_exporting()
            file.close()
