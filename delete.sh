#!/bin/bash
cp database.csv tmp_1
cat delete-me | while read line
do
	echo $line
	# Fix the DB
	sed -e '/^'$line'/d' tmp_1 > tmp_2
	mv tmp_2 tmp_1
	# Remove the files
	rm downloads/$line.info.json
	rm downloads/$line.mp3
done

cp database.csv database.csv_backup
cp tmp_1 database.csv
