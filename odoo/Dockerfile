FROM odoo:12.0

USER root

# Install required Python packages permanently into the image
RUN pip3 install \
    https://github.com/aeroo/aeroolib/archive/refs/heads/master.zip \
    openpyxl \
    num2words \
    f2format

# Copy our custom entrypoint
COPY custom_entrypoint.sh /custom_entrypoint.sh
RUN chmod +x /custom_entrypoint.sh

USER odoo

ENTRYPOINT ["/custom_entrypoint.sh"]
CMD ["odoo"]
