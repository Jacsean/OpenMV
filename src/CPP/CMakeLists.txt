cmake_minimum_required(VERSION 3.10)
project(OpenCVVisionSystem)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找OpenCV包
find_package(OpenCV REQUIRED)

if(NOT OpenCV_FOUND)
    message(FATAL_ERROR "未找到OpenCV库,请先安装OpenCV")
endif()

include_directories(${OpenCV_INCLUDE_DIRS})

# 添加可执行文件
add_executable(vision_system
    main.cpp
    vision_system.cpp
)

# 链接OpenCV库
target_link_libraries(vision_system ${OpenCV_LIBS})

# 设置输出目录
set_target_properties(vision_system PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# 打印配置信息
message(STATUS "OpenCV版本: ${OpenCV_VERSION}")
message(STATUS "OpenCV包含目录: ${OpenCV_INCLUDE_DIRS}")
message(STATUS "OpenCV库: ${OpenCV_LIBS}")
