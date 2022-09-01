# Tongji-AutoGetScore

> 温馨提示：本项目仍在建设中。

自动从同济大学教务网获取成绩并推送邮件通知。

**本项目是：**

- 一个用户友好的、包含GUI的成绩查询解决方案。
- 前端开源、后端闭源（但无偿赠与用户使用）的。

**本项目不是：**

- 易于被开发者二次利用的成绩查询组件/模块。但是，你可以自由地参考或裁剪本项目，使其利于你的开发。



作者：Cinea （信息大类->测绘学院2021级）

纯自学作品，代码写的很丑很不美观，敬请谅解。

## 开源声明

本项目是遵照GPL协议开源的，但是若你有修改/引用本项目的需要，禁止你使用项目中的邮件账户和密码。此外，你可以自由使用/保留项目中的所有web接口。

## 安装使用

### Windows / macOS用户

前往Releases页或我的个人网站下载安装发行版。

配置需求：

- Windows 10/11（Win 7/8请用下方手动安装）
- macOS （等待测试）

### Linux用户/不希望使用发行版的用户

1. 克隆代码

```bash
git clone https://github.com/Cinea4678/Tongji-AutoGetScore.git
```

（若因网络问题无法克隆，请自行搜索并使用镜像站）

2. 安装Python、外部库

   使用你的包管理软件安装Python3。之后，使用pip安装外部库：

```bash
cd Tongji-AutoGetScore
pip3 install -r pipRequirement.txt
```

3. 启动程序

```bash
python3 Tongji-AutoGetScore.py
```



