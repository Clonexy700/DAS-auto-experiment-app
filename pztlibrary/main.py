"""
Configuration Program
---------------------------
Demonstrates multichannel configuration using JSON settings
"""

import time
from usart_lib import SerialConfigurator, load_configuration, USARTError


def main():
    try:
        # Load configuration
        config = load_configuration('config.json')
        config_1 = load_configuration('config1.json')
        config_2 = load_configuration('config2.json')
        config_3 = load_configuration('config3.json')
        config_4 = load_configuration('config4.json')
        config_0 = load_configuration('config_zeroes.json')
        # Initialize and configure
        with SerialConfigurator(port='com4') as sc:
            sc.start_monitoring()
            sc.configure_channels(config)
            time.sleep(1)
            sc.configure_channels(config_1)
            time.sleep(1)
            sc.configure_channels(config_2)
            time.sleep(1)
            sc.configure_channels(config_3)
            time.sleep(1)
            sc.configure_channels(config_4)
            time.sleep(3)
            sc.configure_channels(config_0)#так мы отключаем
            time.sleep(5)
            return
            # Keep alive for monitoring
            while True:
                time.sleep(1)

    except USARTError as e:
        print(f"Error: {str(e)}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")


if __name__ == "__main__":
    main()
