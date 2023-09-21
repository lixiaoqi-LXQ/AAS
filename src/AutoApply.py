from time import sleep
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException


from Config import TIMEOUT, Config, YoungUrl, LogInUrl


class AutoApply:
    """
    自动构建系列子项目
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        service = webdriver.ChromeService(executable_path=config.driver_path)
        self.driver = webdriver.Chrome(service=service)
        self.driver.set_window_size(1024, 768)
        self.wait = WebDriverWait(self.driver, TIMEOUT)

    def __get_calender_date_input(self):
        while True:
            try:
                starts = self.driver.find_elements(
                    By.XPATH, f"//input[@placeholder='开始日期']")
                ends = self.driver.find_elements(
                    By.XPATH, f"//input[@placeholder='结束日期']")
                end = [el for el in ends if not el.get_attribute('readonly')]
                start = [
                    el for el in starts if not el.get_attribute('readonly')]
                assert len(start) == len(end) == 1, '日历尚未打开'
            except (StaleElementReferenceException, AssertionError):
                continue
            else:
                break
        return start[0], end[0]

    def run(self):
        print('连接网页...')
        self.driver.get(YoungUrl)
        self.login()
        # 等待页面加载
        self.until(
            EC.presence_of_all_elements_located((By.XPATH, "//span[text()='欢迎您，{}']".format(self.config.fixed['联系人']))))
        self.make_sure_at(YoungUrl)
        self.access_parent()
        for i in range(self.config.batch_size):
            day_delta = self.config.day_delta * i
            self.create_single(self.config.start_date+day_delta)
        print("成功")

    def create_single(self, day: date):
        sub_activity_name = self.config.format_name(day)
        print(f'创建子项目：{sub_activity_name}')

        # FIXME better way to check if the page loads completely?
        self.until(lambda _: len(
            self.driver.find_elements(By.TAG_NAME, 'tbody')) == 2
        )
        sleep(0.3)
        button = "//button[span='新增']"
        self.driver.find_element(By.XPATH, button).click()
        self.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[text()='新增']")))

        # fill item with placeholders
        find_input_by_placeholder = "//input[@placeholder='{}']"
        for item in self.config.placeholders:
            value = sub_activity_name if item == '名称' else self.config.fixed[item]
            placeholder = self.config.placeholders[item]
            xpath_str = find_input_by_placeholder.format(placeholder)
            target_input = self.driver.find_elements(By.XPATH, xpath_str)[-1]
            target_input.send_keys(value)
            if item == '联系人':
                sleep(1)
            target_input.send_keys(Keys.ENTER)

        # fill intros
        self.driver.switch_to.frame(0)
        self.driver.find_element(By.ID, "tinymce").send_keys(
            self.config.intro_text)
        self.driver.switch_to.parent_frame()
        # and admin-idea
        self.driver.switch_to.frame(1)
        self.driver.find_element(By.ID, "tinymce").send_keys(
            self.config.admin_idea)
        self.driver.switch_to.parent_frame()

        # fill apply range: simulate mouse click
        self.driver.find_element(By.ID, 'applyRange').click()
        self.driver.find_element(
            By.XPATH, f"//li[text()='{self.config.apply_range}']").click()

        # fill the hold time
        self.driver.find_element(By.ID, 'the_time').click()
        start = Config.mix_date_time_to_str(day, self.config.start_time)
        end = Config.mix_date_time_to_str(day, self.config.end_time)
        start_input, end_input = self.__get_calender_date_input()
        end_input.send_keys(end)
        start_input.send_keys(start)
        start_input.send_keys(Keys.ENTER)

        # fill the apply time
        self.driver.find_element(By.ID, 'time').click()
        start = Config.mix_date_time_to_str(
            date.today(), self.config.apply_start_time)
        end = Config.mix_date_time_to_str(day, self.config.apply_end_time)
        start_input, end_input = self.__get_calender_date_input()
        end_input.send_keys(end)
        start_input.send_keys(start)
        start_input.send_keys(Keys.ENTER)

        # fill image: simply simulate mouse clicks
        # FIXME may check if it's an image
        img = self.config.get_image()
        self.driver.find_element(By.CSS_SELECTOR, 'div.picBox').click()
        self.driver.find_element(
            By.CSS_SELECTOR, "input[type='file'][accept='']").send_keys(img)
        self.until(
            lambda _: len(self.driver.find_elements(By.XPATH, "//img[@src='']")) == 0)
        self.driver.find_element(
            By.XPATH, "//button[span[text()='确 定']]").click()

        # finish
        while True:
            try:
                self.driver.find_element(
                    By.XPATH, "//button[span[text()='暂 存']]").click()
            except ElementClickInterceptedException:
                continue
            else:
                break

    def login(self):
        if self.driver.current_url.startswith(LogInUrl):
            print('登录中...')
            username = self.driver.find_element(By.ID, 'username')
            password = self.driver.find_element(By.ID, 'password')
            loginbtn = self.driver.find_element(By.ID, 'login')
            username.send_keys(self.config.student_id)
            password.send_keys(self.config.password)
            loginbtn.click()

    def make_sure_at(self, url):
        if self.driver.current_url != url:
            self.driver.get(url)
        assert self.driver.current_url == url, "现在的url：{}".format(
            self.driver.current_url)

    def access_parent(self):
        """
        假设不会出现翻页寻找母项目的情况
        """
        print("定位母项目...")
        locate_parent_tr = "//tr[td[3]='{}']".format(
            self.config.parent_activity_name)
        try:
            parent_tr = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, locate_parent_tr)))
        except Exception as e:
            print("定位失败，检查配置中母项目名称是否正确")
            raise e
        else:
            parent_tr.find_element(By.LINK_TEXT, "项目实施").click()

    def until(self, *args):
        return self.wait.until(*args)
