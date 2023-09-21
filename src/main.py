import traceback
from Config import Config
from AutoApply import AutoApply


if __name__ == '__main__':
    #  test()
    auto = AutoApply(Config("../config.json"))
    try:
        auto.run()
    except Exception:
        print(traceback.format_exc())
    input("按回车结束")
