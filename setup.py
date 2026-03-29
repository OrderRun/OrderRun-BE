"""Setup configuration for OrderRun backend."""
from setuptools import setup, find_packages

setup(
    name="orderrun",
    version="0.1.0",
    packages=find_packages(include=["app", "app.*"]),
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.32.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.13.0",
        "pymysql>=1.1.0",
        "cryptography>=42.0.0",
        "pydantic>=2.9.0",
        "pydantic-settings>=2.6.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "httpx>=0.27.0",
        "python-multipart>=0.0.9",
        "aiosmtplib>=3.0.0",
        "jinja2>=3.1.0",
        "email-validator>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.24.0",
            "pytest-cov>=5.0.0",
            "httpx>=0.27.0",
            "faker>=30.0.0",
        ]
    },
    python_requires=">=3.12",
)
