import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import threading
import os


class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Price_checker by Trongtranlee")
        self.root.geometry("600x450")

        # Biến để lưu đường dẫn file và website được chọn
        self.input_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()
        self.selected_website = tk.StringVar(value="fptshop")  # Giá trị mặc định

        # Tạo giao diện
        self.create_widgets()

        # Flag để kiểm soát việc dừng scraping
        self.is_running = False

    def create_widgets(self):
        # Frame cho việc chọn website
        website_frame = ttk.LabelFrame(self.root, text="Chọn Website", padding="5")
        website_frame.pack(fill="x", padx=5, pady=5)

        ttk.Radiobutton(website_frame, text="FPT Shop", variable=self.selected_website,
                        value="fptshop").pack(side="left", padx=5)
        ttk.Radiobutton(website_frame, text="Dien May Xanh", variable=self.selected_website,
                        value="dienmayxanh").pack(side="left", padx=5)
        ttk.Radiobutton(website_frame, text="The Gioi Di Dong", variable=self.selected_website,
                        value="thegioididong").pack(side="left", padx=5)

        # Frame cho phần input
        input_frame = ttk.LabelFrame(self.root, text="Input", padding="5")
        input_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(input_frame, text="Chọn File Input", command=self.select_input_file).pack(side="left", padx=5)
        ttk.Label(input_frame, textvariable=self.input_file_path).pack(side="left", padx=5, fill="x", expand=True)

        # Frame cho output
        output_frame = ttk.LabelFrame(self.root, text="Output", padding="5")
        output_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(output_frame, text="Chọn File Output", command=self.select_output_file).pack(side="left", padx=5)
        ttk.Label(output_frame, textvariable=self.output_file_path).pack(side="left", padx=5, fill="x", expand=True)

        # Frame cho các nút điều khiển
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=5, pady=5)

        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_scraping)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_scraping, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(control_frame, length=300, variable=self.progress_var, mode='determinate')
        self.progress.pack(side="left", padx=5, fill="x", expand=True)

        # Khu vực hiển thị log
        log_frame = ttk.LabelFrame(self.root, text="Log", padding="5")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_area.pack(fill="both", expand=True)

    def select_input_file(self):
        filename = filedialog.askopenfilename(
            title="Chọn file input",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file_path.set(filename)

    def select_output_file(self):
        filename = filedialog.asksaveasfilename(
            title="Chọn file output",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.output_file_path.set(filename)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def setup_chrome_options(self):
        """Thiết lập các options cho Chrome để chạy headless"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--window-size=1920,1080")
        return chrome_options

    def start_scraping(self):
        if not self.input_file_path.get() or not self.output_file_path.get():
            self.log("Vui lòng chọn file input và output!")
            return

        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_var.set(0)

        # Chạy scraping trong thread riêng
        thread = threading.Thread(target=self.run_scraper)
        thread.daemon = True
        thread.start()

    def stop_scraping(self):
        self.is_running = False
        self.log("Đang dừng...")

    def scrape_fptshop(self, driver, product_codes, writer):
        """Hàm scraping cho FPTShop"""
        for index, code in enumerate(product_codes):
            if not self.is_running:
                break

            self.log(f"\nĐang xử lý mã: {code}")
            try:
                search_box = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                search_box.clear()
                search_box.send_keys(code)
                search_box.send_keys(Keys.RETURN)
                time.sleep(3)

                try:
                    price = driver.find_element(By.CLASS_NAME, "Price_currentPrice__PBYcv").text
                except:
                    price = "Không tìm thấy"
                    self.log(f"Không tìm thấy giá hiện tại cho mã {code}")

                try:
                    original_price = driver.find_element(By.CLASS_NAME,
                                                         "text-textOnWhiteSecondary.line-through.f1-regular").text
                except:
                    original_price = "Không tìm thấy giá gốc"
                    self.log(f"Không tìm thấy giá gốc cho mã {code}")

                # Ghi log và lưu dữ liệu một lần
                self.log(f"Giá gốc: {original_price}, Giá hiện tại: {price}")
                writer.writerow([code, original_price, price])

                progress = (index + 1) / len(product_codes) * 100
                self.progress_var.set(progress)

            except Exception as e:
                self.log(f"Lỗi khi xử lý mã {code}: {str(e)}")

            time.sleep(2)

    def scrape_dienmayxanh(self, driver, product_names, writer):
        """Hàm scraping cho Điện Máy Xanh"""
        wait = WebDriverWait(driver, 10)

        for index, name in enumerate(product_names):
            if not self.is_running:
                break

            self.log(f"\nĐang xử lý sản phẩm: {name}")
            try:
                search_box = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[placeholder='Bạn tìm gì...']")))
                search_box.clear()
                search_box.send_keys(name)
                search_box.send_keys(Keys.RETURN)
                time.sleep(3)

                try:
                    product_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-price]")))
                    current_price = product_element.get_attribute("data-price")
                    if current_price:
                        current_price = f"{float(current_price):,.0f}₫".replace(",", ".")
                    else:
                        current_price = "Không tìm thấy"
                except:
                    current_price = "Không tìm thấy"

                try:
                    old_price_element = wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "price-old")))
                    old_price = old_price_element.text
                except:
                    old_price = "Không tìm thấy"

                self.log(f"Giá gốc: {old_price}, Giá hiện tại: {current_price}")
                writer.writerow([name, old_price, current_price])

                progress = (index + 1) / len(product_names) * 100
                self.progress_var.set(progress)

            except Exception as e:
                self.log(f"Lỗi khi xử lý sản phẩm {name}: {str(e)}")
                writer.writerow([name, "Lỗi", "Lỗi"])

            time.sleep(2)

    def scrape_thegioididong(self, driver, product_names, writer):
        """Hàm scraping cho the gioi di dong"""
        wait = WebDriverWait(driver, 10)

        for index, name in enumerate(product_names):
            if not self.is_running:
                break

            self.log(f"\nĐang xử lý sản phẩm: {name}")
            try:
                search_box = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[placeholder='Bạn tìm gì...']")))
                search_box.clear()
                search_box.send_keys(name)
                search_box.send_keys(Keys.RETURN)
                time.sleep(3)

                try:
                    product_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-price]")))
                    current_price = product_element.get_attribute("data-price")
                    if current_price:
                        current_price = f"{float(current_price):,.0f}₫".replace(",", ".")
                    else:
                        current_price = "Không tìm thấy"
                except:
                    current_price = "Không tìm thấy"

                try:
                    old_price_element = wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "price-old")))
                    old_price = old_price_element.text
                except:
                    old_price = "Không tìm thấy"

                self.log(f"Giá gốc: {old_price}, Giá hiện tại: {current_price}")
                writer.writerow([name, old_price, current_price])

                progress = (index + 1) / len(product_names) * 100
                self.progress_var.set(progress)

            except Exception as e:
                self.log(f"Lỗi khi xử lý sản phẩm {name}: {str(e)}")
                writer.writerow([name, "Lỗi", "Lỗi"])

            time.sleep(2)

    def run_scraper(self):
        try:
            # Đọc danh sách sản phẩm
            with open(self.input_file_path.get(), 'r', encoding='utf-8') as file:
                products = [line.strip() for line in file if line.strip()]

            if not products:
                self.log("Không có sản phẩm nào trong file input!")
                return

            # Khởi tạo trình duyệt
            chrome_options = self.setup_chrome_options()
            self.log("Đang khởi động Chrome...")
            driver = webdriver.Chrome(options=chrome_options)

            # Mở website tương ứng
            if self.selected_website.get() == "fptshop":
                self.log("Đang truy cập FPTShop...")
                driver.get("https://fptshop.com.vn/")
                header = ['Mã sản phẩm', 'Giá gốc', 'Giá hiện tại']
            elif self.selected_website.get() == "dienmayxanh":
                self.log("Đang truy cập Điện Máy Xanh...")
                driver.get("https://www.dienmayxanh.com/")
                header = ['Mã sản phẩm', 'Giá gốc', 'Giá hiện tại']
            elif self.selected_website.get() == "thegioididong":
                self.log("Đang truy cập The Gioi Di Dong...")
                driver.get("https://www.thegioididong.com/")
                header = ['Mã sản phẩm', 'Giá gốc', 'Giá hiện tại']

            time.sleep(2)

            # Ghi dữ liệu
            with open(self.output_file_path.get(), 'w', newline='', encoding='utf-8-sig') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(header)

                if self.selected_website.get() == "fptshop":
                    self.scrape_fptshop(driver, products, writer)
                elif self.selected_website.get() == "dienmayxanh":
                    self.scrape_dienmayxanh(driver, products, writer)
                elif self.selected_website.get() == "thegioididong":
                    self.scrape_thegioididong(driver, products, writer)

            driver.quit()
            self.log("\nHoàn thành!")

        except Exception as e:
            self.log(f"Lỗi: {str(e)}")

        finally:
            self.is_running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()