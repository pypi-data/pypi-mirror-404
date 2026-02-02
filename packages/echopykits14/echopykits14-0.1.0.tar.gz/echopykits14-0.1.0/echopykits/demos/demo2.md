
## base

```md

# builder
FROM centos:7.9.2009 AS builder

WORKDIR /root/

RUN yum -y install epel-release \
    && yum update -y \
    && yum install -y iproute \
    && yum install -y sudo \
    && echo -e "root\nroot" | passwd root \
    && yum install -y openssh-server \
    # install build tools
    && yum install -y wget make cmake gcc bzip2-devel libffi-devel zlib-devel \
    && yum groupinstall -y "Development Tools" \
    # download, build and install openssl1.1.1
    && wget https://www.openssl.org/source/openssl-1.1.1t.tar.gz \
    && tar xvf openssl-1.1.1t.tar.gz \
    && rm openssl-1.1.1t.tar.gz \
    && cd openssl-1.1.1t \
    && ./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl \
    && make -j $(nproc) \
    && make install \
    && cd .. \
    && rm -rf openssl-1.1.1t \
    && ldconfig \
    && echo "export PATH=/usr/local/openssl/bin:\$PATH" > /etc/profile.d/openssl.sh \
    && echo "export LD_LIBRARY_PATH=/usr/local/openssl/lib:\$LD_LIBRARY_PATH" >> /etc/profile.d/openssl.sh \
    && source /etc/profile.d/openssl.sh \
    # need sqlite3 to build python, solve sqlite3 not found isue
    && yum -y install sqlite-devel \
    # download, build and install python
    && wget https://www.python.org/ftp/python/3.11.2/Python-3.11.2.tgz \
    && tar xvf Python-3.11.2.tgz \
    && rm Python-3.11.2.tgz \
    && cd Python-3.11*/ \
    && LDFLAGS="${LDFLAGS} -Wl,-rpath=/usr/local/openssl/lib" ./configure --with-openssl=/usr/local/openssl  --enable-loadable-sqlite-extensions \
    && make \
    && make altinstall \
    && cd .. \
    && rm -rf Python-3.11* \
    #set python3 alias to python3.11
    && echo "alias python3='/usr/local/bin/python3.11' " >> .bashrc \
    #install git 2 version
    && yum -y remove git \
    && yum -y remove git-* \
    && yum -y install https://packages.endpointdev.com/rhel/7/os/x86_64/endpoint-repo.x86_64.rpm \
    && yum -y install git \
    && yum autoremove -y \
    && yum clean all -y \


docker build -t centos7_python:v1 .


docker container rm -f centos7_python


docker run -dit \
   --network=none \
    --privileged \
   --name centos7_python  \
   centos7_python:v1 \
    /usr/sbin/init
```



## 方式2
> https://www.python.org/ftp/python/3.11.9


```md


# 基础镜像：官方CentOS 7（精简版，更小体积）
FROM centos:7

# 维护者信息（可选）
MAINTAINER echo7 echo@example.com

# 1. 安装依赖：wget（下载压缩包）、tar（解压），并清理yum缓存减小镜像体积
RUN yum install -y wget tar && \
    yum clean all && \
    rm -rf /var/cache/yum/*

# 2. 下载Python 3.11.9 64位Linux二进制源码包（与你提供的地址一致）
RUN wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz

# 3. 解压压缩包（-xf 静默解压，保留原文件结构）
RUN tar -xf Python-3.11.9.tgz

# 4. 进入Python目录，将python3软链接到/usr/local/bin（实现全局调用，无需每次进入目录）
# 软链接后可直接在任意目录执行python3、pip3，替代./python3方式
RUN ln -s /Python-3.11.9/python3 /usr/local/bin/python3 && \
    ln -s /Python-3.11.9/pip3 /usr/local/bin/pip3

# 5. 可选：设置工作目录（后续容器运行时默认进入此目录）
WORKDIR /Python-3.11.9

# 6. 容器启动默认执行命令：查看Python版本（验证运行）
CMD ["python3", "--version"]


```



```sh



docker build -t centos7-python311:v1 .


docker run --rm centos7-python311:v1



# test.py
import sys
print(f"Python版本：{sys.version}")
print(f"运行环境：CentOS 7")



# 宿主机当前目录有test.py，挂载到容器/tmp目录并执行
docker run --rm -v $(pwd):/tmp centos7-python311:v1 python3 /tmp/test.py


```





## two

```md

# 选择基础镜像
FROM python:3.9-alpine

# 设置工作目录
WORKDIR /app

# 复制源代码到容器
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 配置国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 暴露端口
EXPOSE 8000

# 设置启动命令
CMD ["python", "app.py"]

```





##

```

pip download -d flwr_packages -r requirements.txt --platform manylinux2014_x86_64 --only-binary=:all: --python-version 39 --implementation cp


-d 存储包的文件夹
--platform manylinux2014_x86_64 ：指定Linux x64平台
--only-binary=:all: ：只下载二进制包
--python-version 39 ：指定Python版本（这里是3.9）
--implementation cp ：指定CPython实现




安装离线包,使用命令行批量安装
pip install --no-index --find-links ./flwr_packages flwr==1.13.0


```
