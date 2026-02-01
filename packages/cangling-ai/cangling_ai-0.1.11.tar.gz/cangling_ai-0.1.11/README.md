# cangling ai library

## 准备
```shell
pip install twine
pip install build
```

## 编译打包
```shell
pip -m build
```

## 预发布
```shell
python -m twine upload --repository testpypi dist/*
```

## 发布
```shell
python -m twine upload -r nexus dist/*
```

## 使用
```shell
pip install cangling-ai
```



## 发布到repo.cangling.cn
> 在HOME目录下创建 .pypirc 文件
> 内容如下
```toml
[distutils]
index-servers =
    nexus

[nexus]
repository = https://repo.cangling.cn/repository/cangling-py/
username = cangling
password = <PASSWORD>
```

## 客户端配置
Create or edit your pip.conf (Linux/macOS: ~/.config/pip/pip.conf; Windows: %APPDATA%\pip\pip.ini):

```toml
[global]
index-url = https://repo.cangling.cn/repository/pypi-all/simple
trusted-host = repo.cangling.cn
```