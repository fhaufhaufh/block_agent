;; Auto-generated. Do not edit!


(when (boundp 'rm_msgs::Tool_IO_State)
  (if (not (find-package "RM_MSGS"))
    (make-package "RM_MSGS"))
  (shadow 'Tool_IO_State (find-package "RM_MSGS")))
(unless (find-package "RM_MSGS::TOOL_IO_STATE")
  (make-package "RM_MSGS::TOOL_IO_STATE"))

(in-package "ROS")
;;//! \htmlinclude Tool_IO_State.msg.html


(defclass rm_msgs::Tool_IO_State
  :super ros::object
  :slots (_Tool_IO_Mode _Tool_IO_State ))

(defmethod rm_msgs::Tool_IO_State
  (:init
   (&key
    ((:Tool_IO_Mode __Tool_IO_Mode) (let (r) (dotimes (i 2) (push nil r)) r))
    ((:Tool_IO_State __Tool_IO_State) (let (r) (dotimes (i 2) (push nil r)) r))
    )
   (send-super :init)
   (setq _Tool_IO_Mode __Tool_IO_Mode)
   (setq _Tool_IO_State __Tool_IO_State)
   self)
  (:Tool_IO_Mode
   (&optional __Tool_IO_Mode)
   (if __Tool_IO_Mode (setq _Tool_IO_Mode __Tool_IO_Mode)) _Tool_IO_Mode)
  (:Tool_IO_State
   (&optional __Tool_IO_State)
   (if __Tool_IO_State (setq _Tool_IO_State __Tool_IO_State)) _Tool_IO_State)
  (:serialization-length
   ()
   (+
    ;; bool[2] _Tool_IO_Mode
    (* 1    2)
    ;; bool[2] _Tool_IO_State
    (* 1    2)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool[2] _Tool_IO_Mode
     (dotimes (i 2)
       (if (elt _Tool_IO_Mode i) (write-byte -1 s) (write-byte 0 s))
       )
     ;; bool[2] _Tool_IO_State
     (dotimes (i 2)
       (if (elt _Tool_IO_State i) (write-byte -1 s) (write-byte 0 s))
       )
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool[2] _Tool_IO_Mode
   (dotimes (i (length _Tool_IO_Mode))
     (setf (elt _Tool_IO_Mode i) (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
     )
   ;; bool[2] _Tool_IO_State
   (dotimes (i (length _Tool_IO_State))
     (setf (elt _Tool_IO_State i) (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
     )
   ;;
   self)
  )

(setf (get rm_msgs::Tool_IO_State :md5sum-) "8dedcedb3bfd854b3826d29065f33f9d")
(setf (get rm_msgs::Tool_IO_State :datatype-) "rm_msgs/Tool_IO_State")
(setf (get rm_msgs::Tool_IO_State :definition-)
      "bool[2] Tool_IO_Mode          #数字I/O输入/输出状态  0-输入模式，1-输出模式
bool[2] Tool_IO_State         #数字I/O电平状态      0-低，1-高

")



(provide :rm_msgs/Tool_IO_State "8dedcedb3bfd854b3826d29065f33f9d")


