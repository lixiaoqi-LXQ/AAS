import json
import os
import itertools
import locale
from datetime import datetime, timedelta

TIMEOUT = 10


class Config:
    date_fmt = '%Y-%m-%d'
    time_fmt = '%H:%M'

    def __init__(self, config_path):
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        with open(config_path, encoding='utf-8') as config_file:
            self.content = json.load(config_file)
        self.__get_personal()
        self.__get_rely()
        self.__get_activity()

    @classmethod
    def str2time(cls, s):
        return datetime.strptime(s, Config.time_fmt).time()

    @classmethod
    def str2date(cls, s):
        return datetime.strptime(s, Config.date_fmt).date()

    @classmethod
    def mix_date_time_to_str(cls, date, time):
        target = datetime.combine(date, time)
        return target.strftime(Config.date_fmt + " " + Config.time_fmt)

    def get_image(self):
        return next(self.images)

    def format_name(self, date):
        return date.strftime(self.name_fmt).lstrip('0')

    def __get_personal(self):
        personal = self.content['个人信息']
        self.student_id = personal['学号']
        self.password = personal['密码']

    def __get_rely(self):
        config_info = self.content['配置信息']
        self.driver_path = config_info['driver位置']
        assert os.path.exists(
            self.driver_path), "文件'{}'不存在".format(self.driver_path)
        self.login_url = config_info['一卡通登陆网址']
        self.project_create_url = config_info['项目创建网址']

    def __get_activity(self):
        project = self.content['项目信息']
        self.parent_activity_name = project['母项目名称']
        # 固定的信息
        self.fixed = project['固定信息']
        # 根据placeholder寻找input元素
        self.placeholders = project['placeholders']
        # 图片文件夹
        image_dir = self.fixed['图片文件夹']
        assert os.path.isdir(
            image_dir), "图片目录{}不存在".format(image_dir)
        images = [os.path.abspath(os.path.join(image_dir, img))
                  for img in os.listdir(image_dir)]
        self.images = itertools.cycle(images)
        #
        self.name_fmt = self.fixed['名称格式']
        self.intro_text = self.fixed['项目简介']
        self.admin_idea = self.fixed['组织方构想']
        self.apply_range = self.fixed['报名范围']
        # 项目举办时间
        self.start_time = Config.str2time(self.fixed['开始时间'])
        self.end_time = Config.str2time(self.fixed['结束时间'])
        self.apply_start_time = Config.str2time(self.fixed['报名开始时间'])
        self.apply_end_time = Config.str2time(self.fixed['报名结束时间'])
        # 批量创建相关
        batch_info = project['批量创建信息']
        self.batch_size = batch_info['批量创建数量']
        self.day_delta = timedelta(days=batch_info['间隔天数'])
        self.start_date = Config.str2date(batch_info['开始日期'])
