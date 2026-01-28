;; Auto-generated. Do not edit!


(when (boundp 'rm_msgs::Manual_Set_Force_Pose)
  (if (not (find-package "RM_MSGS"))
    (make-package "RM_MSGS"))
  (shadow 'Manual_Set_Force_Pose (find-package "RM_MSGS")))
(unless (find-package "RM_MSGS::MANUAL_SET_FORCE_POSE")
  (make-package "RM_MSGS::MANUAL_SET_FORCE_POSE"))

(in-package "ROS")
;;//! \htmlinclude Manual_Set_Force_Pose.msg.html


(defclass rm_msgs::Manual_Set_Force_Pose
  :super ros::object
  :slots (_pose _joint ))

(defmethod rm_msgs::Manual_Set_Force_Pose
  (:init
   (&key
    ((:pose __pose) "")
    ((:joint __joint) (make-array 0 :initial-element 0 :element-type :integer))
    )
   (send-super :init)
   (setq _pose (string __pose))
   (setq _joint __joint)
   self)
  (:pose
   (&optional __pose)
   (if __pose (setq _pose __pose)) _pose)
  (:joint
   (&optional __joint)
   (if __joint (setq _joint __joint)) _joint)
  (:serialization-length
   ()
   (+
    ;; string _pose
    4 (length _pose)
    ;; int64[] _joint
    (* 8    (length _joint)) 4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _pose
       (write-long (length _pose) s) (princ _pose s)
     ;; int64[] _joint
     (write-long (length _joint) s)
     (dotimes (i (length _joint))
#+(or :alpha :irix6 :x86_64)
       (progn (sys::poke (elt _joint i) (send s :buffer) (send s :count) :long) (incf (stream-count s) 8))
#-(or :alpha :irix6 :x86_64)
       (cond ((and (class (elt _joint i)) (= (length ((elt _joint i) . bv)) 2)) ;; bignum
              (write-long (ash (elt ((elt _joint i) . bv) 0) 0) s)
              (write-long (ash (elt ((elt _joint i) . bv) 1) -1) s))
             ((and (class (elt _joint i)) (= (length ((elt _joint i) . bv)) 1)) ;; big1
              (write-long (elt ((elt _joint i) . bv) 0) s)
              (write-long (if (>= (elt _joint i) 0) 0 #xffffffff) s))
             (t                                         ;; integer
              (write-long (elt _joint i) s)(write-long (if (>= (elt _joint i) 0) 0 #xffffffff) s)))
       )
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _pose
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _pose (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; int64[] _joint
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _joint (instantiate integer-vector n))
     (dotimes (i n)
#+(or :alpha :irix6 :x86_64)
      (setf (elt _joint i) (prog1 (sys::peek buf ptr- :long) (incf ptr- 8)))
#-(or :alpha :irix6 :x86_64)
      (setf (elt _joint i) (let ((b0 (prog1 (sys::peek buf ptr- :integer) (incf ptr- 4)))
                  (b1 (prog1 (sys::peek buf ptr- :integer) (incf ptr- 4))))
              (cond ((= b1 -1) b0)
                     ((and (= b1  0)
                           (<= lisp::most-negative-fixnum b0 lisp::most-positive-fixnum))
                      b0)
                    ((= b1  0) (make-instance bignum :size 1 :bv (integer-vector b0)))
                    (t (make-instance bignum :size 2 :bv (integer-vector b0 (ash b1 1)))))))
     ))
   ;;
   self)
  )

(setf (get rm_msgs::Manual_Set_Force_Pose :md5sum-) "aeeb8895b8a7ffa8296b1f7ab18fb600")
(setf (get rm_msgs::Manual_Set_Force_Pose :datatype-) "rm_msgs/Manual_Set_Force_Pose")
(setf (get rm_msgs::Manual_Set_Force_Pose :definition-)
      "string pose
int64[] joint


")



(provide :rm_msgs/Manual_Set_Force_Pose "aeeb8895b8a7ffa8296b1f7ab18fb600")


