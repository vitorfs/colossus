.PHONY: ensure-data debug release stop clean

debug: ensure-data
	docker compose up --build --detach

release: ensure-data
	docker compose -f docker-compose.yml -f docker-compose.postgres.yml up --build -d

stop:
	docker compose down

clean:
	rm -rf ./data
	docker compose -f docker-compose.yml -f docker-compose.postgres.yml down --volumes --rmi all --remove-orphans

ensure-data:
	mkdir -p ./data
