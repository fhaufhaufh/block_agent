;; Auto-generated. Do not edit!


(when (boundp 'rm_msgs::write_single_register)
  (if (not (find-package "RM_MSGS"))
    (make-package "RM_MSGS"))
  (shadow 'write_single_register (find-package "RM_MSGS")))
(unless (find-package "RM_MSGS::WRITE_SINGLE_REGISTER")
  (make-package "RM_MSGS::WRITE_SINGLE_REGISTER"))

(in-package "ROS")
;;//! \htmlinclude write_single_register.msg.html


(defclass rm_msgs::write_single_register
  :super ros::object
  :slots (_port _address _data _device ))

(defmethod rm_msgs::write_single_register
  (:init
   (&key
    ((:port __port) 0)
    ((:address __address) 0)
    ((:data __data) 0)
    ((:device __device) 0)
    )
   (send-super :init)
   (setq _port (round __port))
   (setq _address (round __address))
   (setq _data (round __data))
   (setq _device (round __device))
   self)
  (:port
   (&optional __port)
   (if __port (setq _port __port)) _port)
  (:address
   (&optional __address)
   (if __address (setq _address __address)) _address)
  (:data
   (&optional __data)
   (if __data (setq _data __data)) _data)
  (:device
   (&optional __device)
   (if __device (setq _device __device)) _device)
  (:serialization-length
   ()
   (+
    ;; int8 _port
    1
    ;; int32 _address
    4
    ;; int16 _data
    2
    ;; int16 _device
    2
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int8 _port
       (write-byte _port s)
     ;; int32 _address
       (write-long _address s)
     ;; int16 _data
       (write-word _data s)
     ;; int16 _device
       (write-word _device s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int8 _port
     (setq _port (sys::peek buf ptr- :char)) (incf ptr- 1)
     (if (> _port 127) (setq _port (- _port 256)))
   ;; int32 _address
     (setq _address (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int16 _data
     (setq _data (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; int16 _device
     (setq _device (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;;
   self)
  )

(setf (get rm_msgs::write_single_register :md5sum-) "967b76240e09e64a48f1fbaa080ed555")
(setf (get rm_msgs::write_single_register :datatype-) "rm_msgs/write_single_register")
(setf (get rm_msgs::write_single_register :definition-)
      "int8 port
int32 address
int16 data
int16 device

")



(provide :rm_msgs/write_single_register "967b76240e09e64a48f1fbaa080ed555")


