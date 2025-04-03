import scrapy
from scrapy.exporters import JsonItemExporter


class CarDataSpider(scrapy.Spider):
    name = "car_data"  # Название для запуска через scrapy crawl car_data
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/uk/legkovie/?page=1"]

    def __init__(self):
        self.file = open('car_data.json', 'wb')
        self.exporter = JsonItemExporter(self.file, ensure_ascii=False)
        self.exporter.start_exporting()

    def parse(self, response):
        # Находим ссылки на страницы объявлений
        car_links = response.xpath(
            "//a[@class='m-link-ticket']/@href").getall()
        for link in car_links:
            yield response.follow(link, self.parse_car)

    def parse_car(self, response):
        # Извлекаем регион и город
        breadcrumbs = response.xpath(
            "//div[@id='breadcrumbs']//div[@class='item']//a/span/text()").getall()
        region = breadcrumbs[2] if len(breadcrumbs) >= 4 else None
        city = breadcrumbs[3] if len(breadcrumbs) >= 4 else None

        # Извлекаем ID авто
        car_id = response.xpath(
            "//ul[@class='mb-10-list unstyle size13 mb-15']//li[contains(text(), 'ID авто')]//span[@class='bold']/text()").get()
        car_id = int(car_id.strip()) if car_id else None

        # Дополнительная информация о машине
        title = response.xpath("//h1/text()").get()
        price = response.xpath("//span[@class='price_value']/text()").get()
        year = response.xpath(
            "//ul[@class='unstyled technical-params']//li[contains(text(), 'Рік')]/span/text()").get()

        # Формируем данные
        data = {
            "id": car_id,
            "region": region,
            "city": city,
            "title": title.strip() if title else None,
            "price": price.strip() if price else None,
            "year": int(year.strip()) if year and year.strip().isdigit() else None
        }

        # Экспортируем в файл
        self.exporter.export_item(data)

        yield data

    def closed(self, reason):
        self.exporter.finish_exporting()
        self.file.close()
