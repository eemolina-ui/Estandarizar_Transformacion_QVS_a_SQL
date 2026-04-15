import React, { useRef, useEffect, useState } from 'react';

const CameraComponent = React.forwardRef(({ isBackground, onToggleBackground }, ref) => {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);

  // Initialize camera stream
  useEffect(() => {
    let mounted = true;

    const startCamera = async () => {
      try {
        // If we already have a stream, don't create a new one
        if (stream) {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
          return;
        }

        const newStream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            width: { ideal: 1920 },
            height: { ideal: 1080 }
          } 
        });
        
        if (mounted) {
          setStream(newStream);
          if (videoRef.current) {
            videoRef.current.srcObject = newStream;
          }
        }
      } catch (err) {
        console.error("Error accessing the camera", err);
      }
    };

    startCamera();

    // Cleanup function
    return () => {
      mounted = false;
      // Don't stop the stream on cleanup - we'll handle that separately
    };
  }, []); // Empty dependency array - only run once on mount

  // Handle stream cleanup on component unmount
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  // Update video reference when switching modes
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [isBackground, stream]);

  const captureImage = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      canvas.getContext('2d').drawImage(videoRef.current, 0, 0);
      return canvas.toDataURL('image/jpeg');
    }
    return null;
  };

  React.useImperativeHandle(ref, () => ({
    captureImage
  }));

  const handleClick = () => {
    if (onToggleBackground) {
      onToggleBackground();
    }
  };

  if (isBackground) {
    return (
      <>
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline
          className="fixed top-0 left-0 w-full h-full object-cover -z-10"
        />
        <button
          onClick={handleClick}
          className="fixed top-4 right-24 bg-[#BBB9DA] hover:bg-[#7874B4] text-white p-4 rounded-md z-50 pointer-events-auto"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-6 h-6"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3"
            />
          </svg>
        </button>
      </>
    );
  }

  return (
    <div 
      className="fixed top-4 right-4 h-20 w-20 rounded-full overflow-hidden cursor-pointer pointer-events-auto"
      onClick={handleClick}
    >
      <video 
        ref={videoRef} 
        autoPlay 
        playsInline
        className="w-full h-full object-cover rounded-lg" 
      />
    </div>
  );
});

export default CameraComponent;