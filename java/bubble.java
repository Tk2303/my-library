public class bubble{
    public static void bubblesort(int ar[]){
        for(int i=0;i<ar.length-1;i++){
            for(int j=0;j<ar.length-1-i;j++){
                if(ar[j]>ar[j+1]){
                    int temp=ar[j];
                    ar[j]=ar[j+1];
                    ar[j+1]=temp;
                }
            }
        }
    }
    public static void selectionsort(int ar[]){
        for(int i=0;i<ar.length-1;i++){
            int min=i;
            for(int j=i+1;j<ar.length;j++){
                if(ar[j]<ar[min]){
                    min=j;
                }
            }
            int temp=ar[min];
            ar[min  ]=ar[i];
            ar[i]=temp;
        }
    }
    public static void print(int ar[]){
        for(int i=0;i<ar.length;i++){
            System.out.print(ar[i]);
        }
    }
    public static void main(String args[]){
        int ar[]={5,4,6,2,1,3};
        selectionsort(ar);
        print(ar);
    }
}