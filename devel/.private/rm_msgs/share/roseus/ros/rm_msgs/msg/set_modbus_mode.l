;; Auto-generated. Do not edit!


(when (boundp 'rm_msgs::set_modbus_mode)
  (if (not (find-package "RM_MSGS"))
    (make-package "RM_MSGS"))
  (shadow 'set_modbus_mode (find-package "RM_MSGS")))
(unless (find-package "RM_MSGS::SET_MODBUS_MODE")
  (make-package "RM_MSGS::SET_MODBUS_MODE"))

(in-package "ROS")
;;//! \htmlinclude set_modbus_mode.msg.html


(defclass rm_msgs::set_modbus_mode
  :super ros::object
  :slots (_port _baudrate _timeout ))

(defmethod rm_msgs::set_modbus_mode
  (:init
   (&key
    ((:port __port) 0)
    ((:baudrate __baudrate) 0)
    ((:timeout __timeout) 0)
    )
   (send-super :init)
   (setq _port (round __port))
   (setq _baudrate (round __baudrate))
   (setq _timeout (round __timeout))
   self)
  (:port
   (&optional __port)
   (if __port (setq _port __port)) _port)
  (:baudrate
   (&optional __baudrate)
   (if __baudrate (setq _baudrate __baudrate)) _baudrate)
  (:timeout
   (&optional __timeout)
   (if __timeout (setq _timeout __timeout)) _timeout)
  (:serialization-length
   ()
   (+
    ;; int8 _port
    1
    ;; int32 _baudrate
    4
    ;; int16 _timeout
    2
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int8 _port
       (write-byte _port s)
     ;; int32 _baudrate
       (write-long _baudrate s)
     ;; int16 _timeout
       (write-word _timeout s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int8 _port
     (setq _port (sys::peek buf ptr- :char)) (incf ptr- 1)
     (if (> _port 127) (setq _port (- _port 256)))
   ;; int32 _baudrate
     (setq _baudrate (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int16 _timeout
     (setq _timeout (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;;
   self)
  )

(setf (get rm_msgs::set_modbus_mode :md5sum-) "6163070760cb79680dfbd36751deebbe")
(setf (get rm_msgs::set_modbus_mode :datatype-) "rm_msgs/set_modbus_mode")
(setf (get rm_msgs::set_modbus_mode :definition-)
      "int8 port
int32 baudrate
int16 timeout
")



(provide :rm_msgs/set_modbus_mode "6163070760cb79680dfbd36751deebbe")


