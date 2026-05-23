#!/usr/bin/env python3
from PIL import Image

# Crop petrochina_gas to 256x256 (center crop from 266x256)
img = Image.open('petrochina_gas.png')
print(f'Original petrochina_gas size: {img.size}')

width, height = img.size
new_size = 256
left = (width - new_size) // 2
top = (height - new_size) // 2
right = left + new_size
bottom = top + new_size

cropped = img.crop((left, top, right, bottom))
cropped.save('petrochina_gas.png', 'PNG', optimize=True)
print(f'Cropped petrochina_gas size: {cropped.size}')

# Generate @2x versions (512x512)
for name in ['kunming_water.png', 'petrochina_gas.png']:
    img = Image.open(name)
    img_2x = img.resize((512, 512), Image.Resampling.LANCZOS)
    base_name = name.replace('.png', '')
    img_2x.save(f'{base_name}@2x.png', 'PNG', optimize=True)
    print(f'Generated {base_name}@2x.png: {img_2x.size}')

print('\nAll files processed successfully!')
