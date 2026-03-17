;; Auto-generated. Do not edit!


(when (boundp 'rm_msgs::write_register)
  (if (not (find-package "RM_MSGS"))
    (make-package "RM_MSGS"))
  (shadow 'write_register (find-package "RM_MSGS")))
(unless (find-package "RM_MSGS::WRITE_REGISTER")
  (make-package "RM_MSGS::WRITE_REGISTER"))

(in-package "ROS")
;;//! \htmlinclude write_register.msg.html


(defclass rm_msgs::write_register
  :super ros::object
  :slots (_port _address _num _data _device ))

(defmethod rm_msgs::write_register
  (:init
   (&key
    ((:port __port) 0)
    ((:address __address) 0)
    ((:num __num) 0)
    ((:data __data) (make-array 0 :initial-element 0 :element-type :integer))
    ((:device __device) 0)
    )
   (send-super :init)
   (setq _port (round __port))
   (setq _address (round __address))
   (setq _num (round __num))
   (setq _data __data)
   (setq _device (round __device))
   self)
  (:port
   (&optional __port)
   (if __port (setq _port __port)) _port)
  (:address
   (&optional __address)
   (if __address (setq _address __address)) _address)
  (:num
   (&optional __num)
   (if __num (setq _num __num)) _num)
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
    ;; int32 _num
    4
    ;; int64[] _data
    (* 8    (length _data)) 4
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
     ;; int32 _num
       (write-long _num s)
     ;; int64[] _data
     (write-long (length _data) s)
     (dotimes (i (length _data))
#+(or :alpha :irix6 :x86_64)
       (progn (sys::poke (elt _data i) (send s :buffer) (send s :count) :long) (incf (stream-count s) 8))
#-(or :alpha :irix6 :x86_64)
       (cond ((and (class (elt _data i)) (= (length ((elt _data i) . bv)) 2)) ;; bignum
              (write-long (ash (elt ((elt _data i) . bv) 0) 0) s)
              (write-long (ash (elt ((elt _data i) . bv) 1) -1) s))
             ((and (class (elt _data i)) (= (length ((elt _data i) . bv)) 1)) ;; big1
              (write-long (elt ((elt _data i) . bv) 0) s)
              (write-long (if (>= (elt _data i) 0) 0 #xffffffff) s))
             (t                                         ;; integer
              (write-long (elt _data i) s)(write-long (if (>= (elt _data i) 0) 0 #xffffffff) s)))
       )
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
   ;; int32 _num
     (setq _num (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int64[] _data
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _data (instantiate integer-vector n))
     (dotimes (i n)
#+(or :alpha :irix6 :x86_64)
      (setf (elt _data i) (prog1 (sys::peek buf ptr- :long) (incf ptr- 8)))
#-(or :alpha :irix6 :x86_64)
      (setf (elt _data i) (let ((b0 (prog1 (sys::peek buf ptr- :integer) (incf ptr- 4)))
                  (b1 (prog1 (sys::peek buf ptr- :integer) (incf ptr- 4))))
              (cond ((= b1 -1) b0)
                     ((and (= b1  0)
                           (<= lisp::most-negative-fixnum b0 lisp::most-positive-fixnum))
                      b0)
                    ((= b1  0) (make-instance bignum :size 1 :bv (integer-vector b0)))
                    (t (make-instance bignum :size 2 :bv (integer-vector b0 (ash b1 1)))))))
     ))
   ;; int16 _device
     (setq _device (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;;
   self)
  )

(setf (get rm_msgs::write_register :md5sum-) "c8a7fd89d42532c5e773df22285bd878")
(setf (get rm_msgs::write_register :datatype-) "rm_msgs/write_register")
(setf (get rm_msgs::write_register :definition-)
      "int8 port
int32 address
int32 num
int64[] data
int16 device

")



(provide :rm_msgs/write_register "c8a7fd89d42532c5e773df22285bd878")


