from setuptools import setup, find_packages

setup(
    name="fikra",
    version="0.2.0",
    description="The Lacesse Edge AI SDK. Offline reasoning.",
    author="Lacesse Ventures",
    author_email="jbm@lacesse.app",
    packages=find_packages(),
    install_requires=[
        "llama-cpp-python>=0.2.23",
        "huggingface_hub>=0.19.0"
    ],
    python_requires='>=3.8',
)
