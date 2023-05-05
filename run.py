from app import create_app

config_class = "config.DevelopmentConfig"
app = create_app(config_class)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
