
services:
  prestserv:
    image: prestserv:1.0
    container_name: prestserv
    restart: unless-stopped
    init: true

    working_dir: /app

    volumes:
      - /server/containers/PrestServ/PrestServ:/app

    environment:
      TZ: America/Sao_Paulo
      PYTHONUNBUFFERED: "1"
      PYTHONDONTWRITEBYTECODE: "1"
    
      STREAMLIT_BROWSER_SERVER_ADDRESS: "pdf.ksenos.space"
      STREAMLIT_BROWSER_SERVER_PORT: "443"

    expose:
      - "8501"

    networks:
      - homelab_proxy

networks:
  homelab_proxy:
    external: true
