FROM ubuntu:20.04

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dirmngr \
    fonts-noto-cjk \
    gnupg \
    libssl-dev \
    node-less \
    npm \
    python3-num2words \
    python3-pil \
    python3-pip \
    python3-phonenumbers \
    python3-qrcode \
    python3-renderpm \
    python3-setuptools \
    python3-slugify \
    python3-vobject \
    python3-watchdog \
    python3-xlrd \
    python3-xlwt \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf (focal/Ubuntu 20.04 version)
RUN curl -o wkhtmltox.deb -sSL \
    https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

# Install rtlcss
RUN npm install -g rtlcss

# Install Odoo 12 from official nightly .deb (compatible with Python 3.8)
RUN curl -o odoo.deb -sSL http://nightly.odoo.com/12.0/nightly/deb/odoo_12.0.latest_all.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends ./odoo.deb \
    && rm -rf /var/lib/apt/lists/* odoo.deb

# Install extra Python packages required by custom modules
RUN pip3 install \
    https://github.com/aeroo/aeroolib/archive/refs/heads/master.zip \
    openpyxl \
    num2words

# Setup extra-addons directory
RUN mkdir -p /mnt/extra-addons \
    && useradd -ms /bin/bash odoo 2>/dev/null || true \
    && chown -R odoo /mnt/extra-addons \
    && mkdir -p /var/lib/odoo && chown -R odoo /var/lib/odoo \
    && mkdir -p /etc/odoo && chown -R odoo /etc/odoo

# Copy our custom entrypoint
COPY custom_entrypoint.sh /custom_entrypoint.sh
RUN chmod +x /custom_entrypoint.sh

VOLUME ["/var/lib/odoo", "/mnt/extra-addons"]
EXPOSE 8069 8071 8072

ENV ODOO_RC=/etc/odoo/odoo.conf

USER odoo
ENTRYPOINT ["/custom_entrypoint.sh"]
CMD ["odoo"]
