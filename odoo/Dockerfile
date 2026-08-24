FROM debian:buster-slim

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

ENV LANG C.UTF-8

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

# Install wkhtmltopdf (buster version)
RUN curl -o wkhtmltox.deb -sSL \
    https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.buster_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

# Install rtlcss for RTL language support
RUN npm install -g rtlcss

# Install Odoo 12 from official nightly .deb (works with Python 3.7)
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
    && chown -R odoo /mnt/extra-addons

# Copy our custom entrypoint (fixes f-strings before Odoo starts)
COPY custom_entrypoint.sh /custom_entrypoint.sh
RUN chmod +x /custom_entrypoint.sh

VOLUME ["/var/lib/odoo", "/mnt/extra-addons"]
EXPOSE 8069 8071 8072

ENV ODOO_RC /etc/odoo/odoo.conf

USER odoo
ENTRYPOINT ["/custom_entrypoint.sh"]
CMD ["odoo"]
