library(tidyverse)
prods <- read.csv("../data/stationery.csv", strip.white = TRUE, stringsAsFactors = FALSE)
sh_brands <- prods %>% select(brand) %>% unique %>% arrange(brand)
supraano_brands <- read.csv("../data/supraano_db_brands.csv", strip.white = TRUE,
                            colClasses = "character") %>% filter(status == 1)
sh_only_brands <- tibble(brand = setdiff(sh_brands$brand, supraano_brands$name))
#write_csv(sh_only_brands, "data/only_shahrvand.csv")
brand_map <- read.csv("data/brand_map.csv", strip.white = TRUE, colClasses = "character") 
## check for duplicate brands
dup_sup <- supraano_brands[duplicated(supraano_brands$name),]
dup_sh_ids <- foods[duplicated(foods$shahrvand_id), ]$shahrvand_id
dup_sh <- foods %>% filter(shahrvand_id %in% dup_sh_ids)

## join the tables and find corresponing Supraano brands
#brand_map <- brand_map %>% filter(shahrvand_brand != supraano_brand)
brand_map <- brand_map %>% right_join(sh_brands, by = c("shahrvand_brand" = "brand"))
brand_map[is.na(brand_map$supraano_brand), "supraano_brand"] <- 
    brand_map[is.na(brand_map$supraano_brand), "shahrvand_brand"]
brand_map <- brand_map %>% left_join(supraano_brands[ ,c("id", "name")],
                                     by = c("supraano_brand" = "name"))
## make sure all the items have a corresponding supraano id
null_id <- brand_map[is.na(brand_map$id),]
if (nrow(null_id) > 0)
  stop("There are items with a null brand id.")
write.csv(brand_map, "data/brand_map_full.csv", row.names = FALSE)

## now test on all the items
foods <- foods %>% left_join(brand_map[, c("shahrvand_brand", "id")],
                             by = c("brand" = "shahrvand_brand"))

# in_both <- data.frame(title = intersect(supraano_brands$name, shahrvand_brands$title))
# shahrvand_only = data.frame(title = setdiff(shahrvand_brands$title, supraano_brands$name))
# supraano_only = data.frame(title = setdiff(supraano_brands$name, shahrvand_brands$title))
# write_csv(in_both, "data/in_both.csv")
# write_csv(shahrvand_only, "data/shahrvand_only.csv")
# write_csv(supraano_only, "data/supraano_only.csv")
