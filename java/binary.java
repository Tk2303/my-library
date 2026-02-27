public class binary{
    public static int BinarySearch(int num[],int key){
        int low=0;
        int high=num.length-1;
        while(low<=high){
            int mid=(low+high)/2;
            if(num[mid]==key){
                return mid;
            }
            else if(num[mid]<key){
                high=mid-1;

            }
            else{
                low=mid+1;
            }
        }
        return -1;
    }
    public static void main(String args[]){
        int num[]= {4,5,6,7, 0, 1, 2};
        int key=0;
        int result=BinarySearch(num,key);
        if(result==-1){
            System.out.println("Element not found");
        }
        else{
            System.out.println("Element found at index:"+result);
        }
    }
}