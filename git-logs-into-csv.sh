echo "commit id,author,date,comment,changed files,lines added,lines deleted" > res.csv 
git log --date=format:'%Y-%m-%d %H:%M' --all --pretty="%x40%h%x2C%an%x2C%ad%x2C%x22%s%x22%x2C" --shortstat | tr "\n" " " | tr "@" "\n" >> res.csv
sed -i 's/ files changed//g' res.csv
sed -i 's/ file changed//g' res.csv
sed -i 's/ insertions(+)//g' res.csv
sed -i 's/ insertion(+)//g' res.csv
sed -i 's/ deletions(-)//g' res.csv
sed -i 's/ deletion(-)//g' res.csv
