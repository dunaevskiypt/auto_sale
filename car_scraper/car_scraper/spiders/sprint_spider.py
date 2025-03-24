import scrapy


class SprintParser(scrapy.Spider):
    name = "sprint_spider"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/legkovie/?page=121"
    ]

    def parse(self, response):
        # Parse only brand and model
        for item in response.css("section.ticket-item"):
            # Extract brand and model from the <a> tag with class 'address'
            title = item.css("a.address::attr(title)").get()
            if title:
                # Title format is like "Toyota Venza 2013 in Kyiv"
                # Split by spaces to separate brand and model
                title_parts = title.split(" ", 2)
                brand = title_parts[0]
                model = title_parts[1] if len(title_parts) > 1 else None
            else:
                brand, model = None, None

            data = {
                "id": item.attrib.get("data-advertisement-id"),
                "brand": brand,
                "model": model,
            }
            yield data
