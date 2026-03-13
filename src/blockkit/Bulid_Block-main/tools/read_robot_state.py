import time
from airbot_py.arm import AIRBOTPlay

def main():
    # 机械臂 IP 地址，请根据实际情况修改
    # 默认通常是 "192.168.1.135" 或 "localhost" (如果是在板载计算机上运行)
    # 根据之前的 cali.py，这里使用 "192.168.1.135" 作为默认值，但如果是在本机运行，可能需要改为 "localhost"
    # 如果连接失败，请尝试 "localhost"
    ROBOT_IP = "localhost" 
    ROBOT_PORT = 50000 # 注意：cali.py 中使用的是 50000，SDK 文档默认是 50051，这里沿用 cali.py 的配置

    print(f"正在连接机械臂 ({ROBOT_IP}:{ROBOT_PORT})...")
    
    try:
        # 使用 with 语句自动管理连接和断开
        # 如果是在板载电脑上运行，url 通常设为 "localhost"
        # 如果是远程控制，url 设为机械臂 IP
        with AIRBOTPlay(url=ROBOT_IP, port=ROBOT_PORT) as robot:
            print("连接成功！")
            
            # 获取当前关节角度
            joint_pos = robot.get_joint_pos()
            
            if joint_pos:
                print("\n当前关节角度 (弧度):")
                print(f"{joint_pos}")
                
                print("\n当前关节角度 (度):")
                degrees = [round(x * 57.29578, 2) for x in joint_pos]
                print(f"{degrees}")
            else:
                print("无法获取关节角度。")
                
    except Exception as e:
        print(f"发生错误: {e}")
        print("提示: 如果连接失败，请检查 IP 地址和端口号。")
        print("      如果是在机械臂自带的电脑上运行，请尝试将 IP 改为 'localhost'。")

if __name__ == "__main__":
    main()
