;; Auto-generated. Do not edit!


(when (boundp 'blockkit::ObjectInfo)
  (if (not (find-package "BLOCKKIT"))
    (make-package "BLOCKKIT"))
  (shadow 'ObjectInfo (find-package "BLOCKKIT")))
(unless (find-package "BLOCKKIT::OBJECTINFO")
  (make-package "BLOCKKIT::OBJECTINFO"))

(in-package "ROS")
;;//! \htmlinclude ObjectInfo.msg.html


(defclass blockkit::ObjectInfo
  :super ros::object
  :slots (_object_class _x _y _z ))

(defmethod blockkit::ObjectInfo
  (:init
   (&key
    ((:object_class __object_class) "")
    ((:x __x) 0.0)
    ((:y __y) 0.0)
    ((:z __z) 0.0)
    )
   (send-super :init)
   (setq _object_class (string __object_class))
   (setq _x (float __x))
   (setq _y (float __y))
   (setq _z (float __z))
   self)
  (:object_class
   (&optional __object_class)
   (if __object_class (setq _object_class __object_class)) _object_class)
  (:x
   (&optional __x)
   (if __x (setq _x __x)) _x)
  (:y
   (&optional __y)
   (if __y (setq _y __y)) _y)
  (:z
   (&optional __z)
   (if __z (setq _z __z)) _z)
  (:serialization-length
   ()
   (+
    ;; string _object_class
    4 (length _object_class)
    ;; float64 _x
    8
    ;; float64 _y
    8
    ;; float64 _z
    8
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _object_class
       (write-long (length _object_class) s) (princ _object_class s)
     ;; float64 _x
       (sys::poke _x (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _y
       (sys::poke _y (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _z
       (sys::poke _z (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _object_class
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _object_class (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float64 _x
     (setq _x (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _y
     (setq _y (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _z
     (setq _z (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;;
   self)
  )

(setf (get blockkit::ObjectInfo :md5sum-) "3fb8ba78b5949ec9fd9b6e9dd65602ad")
(setf (get blockkit::ObjectInfo :datatype-) "blockkit/ObjectInfo")
(setf (get blockkit::ObjectInfo :definition-)
      "string object_class  
float64 x            
float64 y            
float64 z 

")



(provide :blockkit/ObjectInfo "3fb8ba78b5949ec9fd9b6e9dd65602ad")


