from phone_sensor import PhoneSensor
from matplotlib import pyplot as plt

# Hosts a webserver in a background thread.
# Display a QR code link to the app
phone = PhoneSensor(qrcode=True)

# wait for button press to snap a photo
img = phone.grab(button=True)
# get device orientation as a Quaternion
quaternion = phone.imu().quaternion

plt.subplot(1, 2, 1)
plt.imshow(img)
plt.subplot(1, 2, 2)
plt.bar(['x', 'y', 'z', 'w'], quaternion)
plt.show()
