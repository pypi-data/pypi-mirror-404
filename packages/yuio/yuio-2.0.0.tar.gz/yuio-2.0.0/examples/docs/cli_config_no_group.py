import yuio.app
import yuio.config

class ExecutorConfig(yuio.config.Config):
    #: Number of threads to use.
    threads: int = 4
    #: Enable gpu usage.
    use_gpu: bool = True

@yuio.app.app
def main(
    executor_config: ExecutorConfig = yuio.app.inline(
        help_group=None  # [1]_
    ),
):
    ...

if __name__ == "__main__":
    main.run()
