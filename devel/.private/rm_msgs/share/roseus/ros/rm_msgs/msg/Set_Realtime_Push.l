;; Auto-generated. Do not edit!


(when (boundp 'rm_msgs::Set_Realtime_Push)
  (if (not (find-package "RM_MSGS"))
    (make-package "RM_MSGS"))
  (shadow 'Set_Realtime_Push (find-package "RM_MSGS")))
(unless (find-package "RM_MSGS::SET_REALTIME_PUSH")
  (make-package "RM_MSGS::SET_REALTIME_PUSH"))

(in-package "ROS")
;;//! \htmlinclude Set_Realtime_Push.msg.html


(defclass rm_msgs::Set_Realtime_Push
  :super ros::object
  :slots (_cycle _port _force_coordinate _ip ))

(defmethod rm_msgs::Set_Realtime_Push
  (:init
   (&key
    ((:cycle __cycle) 0)
    ((:port __port) 0)
    ((:force_coordinate __force_coordinate) 0)
    ((:ip __ip) "")
    )
   (send-super :init)
   (setq _cycle (round __cycle))
   (setq _port (round __port))
   (setq _force_coordinate (round __force_coordinate))
   (setq _ip (string __ip))
   self)
  (:cycle
   (&optional __cycle)
   (if __cycle (setq _cycle __cycle)) _cycle)
  (:port
   (&optional __port)
   (if __port (setq _port __port)) _port)
  (:force_coordinate
   (&optional __force_coordinate)
   (if __force_coordinate (setq _force_coordinate __force_coordinate)) _force_coordinate)
  (:ip
   (&optional __ip)
   (if __ip (setq _ip __ip)) _ip)
  (:serialization-length
   ()
   (+
    ;; uint16 _cycle
    2
    ;; uint16 _port
    2
    ;; uint16 _force_coordinate
    2
    ;; string _ip
    4 (length _ip)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; uint16 _cycle
       (write-word _cycle s)
     ;; uint16 _port
       (write-word _port s)
     ;; uint16 _force_coordinate
       (write-word _force_coordinate s)
     ;; string _ip
       (write-long (length _ip) s) (princ _ip s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; uint16 _cycle
     (setq _cycle (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; uint16 _port
     (setq _port (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; uint16 _force_coordinate
     (setq _force_coordinate (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; string _ip
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _ip (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(setf (get rm_msgs::Set_Realtime_Push :md5sum-) "9a0e0df44121dc8d27005a2fbd40ac91")
(setf (get rm_msgs::Set_Realtime_Push :datatype-) "rm_msgs/Set_Realtime_Push")
(setf (get rm_msgs::Set_Realtime_Push :definition-)
      "uint16 cycle
uint16 port
uint16 force_coordinate
string ip
")



(provide :rm_msgs/Set_Realtime_Push "9a0e0df44121dc8d27005a2fbd40ac91")


