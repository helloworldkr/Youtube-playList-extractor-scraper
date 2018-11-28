 
import scrapy  
import re
import pickle
import json
import sys
from scrapy.http import HtmlResponse



class firstSpider(scrapy.Spider): 
   pageScollCount = 0 
   countOfDataPushed = 0
   loopCount = 0
   allData = []
   name = "scrapePlaylist" 
   localHost = "http://localhost:8050/render.html?url="
   youtubeUrl = "https://www.youtube.com/user/physicsgalaxy74/playlists"
   start_urls = [localHost + youtubeUrl]

   def start_requests(self):
      for url in self.start_urls:
         yield scrapy.Request(url, self.parse)
      

   def parse(self, response): 
      print("loop count in the beginning is "+ str(self.loopCount))
      if not 'browse_ajax' in response.url:
         urlForScroll = self.handleFirstResponse(response)
         yield scrapy.Request(urlForScroll, callback=self.parse)
      else:
         nextScrollUrl  = self.handleScrollResponse(response)
         yield scrapy.Request(nextScrollUrl , callback = self.parse)

      

   def handleFirstResponse(self ,response):
      HTMLbodyForSearch = response.body.decode("utf-8")
      pattern = r"continuation\":(.+?\")"
      continuationToken = (re.search(pattern , HTMLbodyForSearch , re.MULTILINE).group(1)).replace('"','')

      playlistnames= response.css('a.yt-simple-endpoint.style-scope.yt-formatted-string::text').extract()
      playlistUrls = response.css('a.yt-simple-endpoint.style-scope.yt-formatted-string::attr(href)').extract()

      self.addNameUrlToData(playlistnames, playlistUrls)

      urlForscroll = "https://www.youtube.com/browse_ajax?ctoken=" + continuationToken
      print("final scroll url \n" + urlForscroll)
      return urlForscroll
      

   def handleScrollResponse(self , response):
      print("inside of scroll response")
      # print(response.url)
      self.pageScollCount = self.pageScollCount +  1
      print("scroll tiems "+ str(self.pageScollCount))
      jsonResponse = json.loads(response.text)
      loadMoreDatafromHtml = jsonResponse['load_more_widget_html']
      contentHTML = jsonResponse['content_html']
      scrollHtmlBody =  HtmlResponse(url="testing", body = contentHTML ,  encoding= 'utf-8')        
      playlistNames = scrollHtmlBody.css('a.yt-uix-sessionlink.yt-uix-tile-link.spf-link.yt-ui-ellipsis.yt-ui-ellipsis-2::attr(title)').extract()  
      playlistUrls = scrollHtmlBody.css('a.yt-uix-sessionlink.yt-uix-tile-link.spf-link.yt-ui-ellipsis.yt-ui-ellipsis-2::attr(href)').extract()  
      
      self.addNameUrlToData(playlistNames, playlistUrls )
      htmlInAjaxCall = jsonResponse['content_html']
      pattern = r";continuation=(.+?)\""
      try:
         next_continuationToken = (re.search(pattern , loadMoreDatafromHtml , re.MULTILINE).group(1))
         if next_continuationToken:
            urlForscroll = "https://www.youtube.com/browse_ajax?ctoken=" + next_continuationToken
            return urlForscroll
      except Exception as e:
         print("got caught in exception ")
         print(e)
         self.writeDataToFile()


   def writeDataToFile(self):
      jsonData = json.dumps( self.allData )
      print("size of item gathered "+ str(len(self.allData)))
      with open("lol.json", 'a') as outfile:
         json.dump( jsonData, outfile)
      self.countOfDataPushed = self.countOfDataPushed + len(self.allData)
      print("count of data pushed "+ str(self.countOfDataPushed))


   def addNameUrlToData(self , playlistnames, playlistUrls): 
      print("length of playlist is " + str(len(playlistnames)))
      for playlistname , url in zip(playlistnames , playlistUrls):
         item = {}
         self.loopCount = self.loopCount + 1
         if 'full playlist' in playlistname:
            continue
         item['playlist']= playlistname
         item['url'] = url
         item['playlistID'] = self.extractPlaylistIdFromUrl(url)
         self.allData.append(item)
      print("total loop count "+ str(self.loopCount))

   def extractPlaylistIdFromUrl(self , url):
      regex = r"list=(.*)"
      playlistID = (re.search(regex , url , re.MULTILINE).group(1))
      return playlistID

      

