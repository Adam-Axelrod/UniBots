from setuptools import find_packages, setup

package_name = 'bot_brain'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gautam',
    maintainer_email='gautambm004@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        'brain = bot_brain.logic.brain_run:main',
        'tof = bot_brain.inputs.tof_run:main',
        'camera = bot_brain.inputs.cam_run:main',
        'yolo = bot_brain.inputs.yolo_run:main',
        'imu = bot_brain.inputs.imu_run:main',
        'motor = bot_brain.outputs.motor_run:main',
        'april = bot_brain.inputs.april_run:main',
        ],
    },
)
