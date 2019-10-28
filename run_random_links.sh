# This script is used to generate and store "used links" 
# that are distributed by the PSF.
cd data
git pull
cd ..
git pull
python tools/random_link.py tools/used_links.txt
git add tools/used_links.txt
git commit -m "Add used links"
git push origin HEAD

